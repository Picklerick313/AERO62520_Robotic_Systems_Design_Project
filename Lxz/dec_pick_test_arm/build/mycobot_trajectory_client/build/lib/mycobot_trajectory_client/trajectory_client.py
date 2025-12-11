#!/usr/bin/env python3
"""
Robot Driver - Runs on myCobot280Pi
Receives trajectories from PC and executes on hardware
Based on: elephantrobotics/mycobot_ros2, pymycobot library
"""

import math
import time
from threading import Thread, Lock
from typing import List, Optional

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState
from std_msgs. msg import Float64, Header

# Import pymycobot - install with: pip install pymycobot
try:
    from pymycobot.mycobot import MyCobot
    PYMYCOBOT_AVAILABLE = True
except ImportError:
    PYMYCOBOT_AVAILABLE = False
    print("Warning: pymycobot not installed.  Run: pip install pymycobot")


class MyCobotRobotDriver(Node):
    """Robot-side driver that receives and executes trajectories."""

    JOINT_NAMES = [
        'joint2_to_joint1',
        'joint3_to_joint2',
        'joint4_to_joint3',
        'joint5_to_joint4',
        'joint6_to_joint5',
        'joint6output_to_joint6'
    ]

    def __init__(self):
        super().__init__('mycobot_robot_driver')
        
        # Declare parameters
        self. declare_parameter('port', '/dev/ttyAMA0')
        self.declare_parameter('baud', 1000000)
        self.declare_parameter('publish_rate', 20.0)
        
        port = self.get_parameter('port').value
        baud = self.get_parameter('baud').value
        publish_rate = self.get_parameter('publish_rate').value
        
        self.callback_group = ReentrantCallbackGroup()
        self.lock = Lock()
        
        # Initialize robot connection
        self.mc = None
        if PYMYCOBOT_AVAILABLE:
            try:
                self. mc = MyCobot(port, baud)
                time.sleep(0.5)
                self.get_logger().info(f'Connected to myCobot on {port}')
            except Exception as e:
                self. get_logger().error(f'Failed to connect: {e}')
        else:
            self. get_logger().warn('Running in simulation mode (no pymycobot)')

        # Current joint positions (radians)
        self.current_positions = [0.0] * 6
        
        # Joint state publisher
        self. joint_state_pub = self.create_publisher(
            JointState,
            '/joint_states',
            10
        )
        
        # Gripper command subscriber
        self.gripper_sub = self.create_subscription(
            Float64,
            '/gripper_controller/command',
            self._gripper_callback,
            10
        )
        
        # Trajectory action server
        self. action_server = ActionServer(
            self,
            FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory',
            self._execute_trajectory_callback,
            callback_group=self.callback_group
        )
        
        # Timer to publish joint states
        self.create_timer(1.0 / publish_rate, self._publish_joint_states)
        
        self.get_logger(). info('myCobot Robot Driver ready!')

    def _publish_joint_states(self):
        """Read and publish current joint states."""
        with self.lock:
            if self.mc is not None:
                try:
                    angles = self.mc. get_angles()
                    if angles and len(angles) == 6:
                        # Convert degrees to radians
                        self.current_positions = [
                            math.radians(a) for a in angles
                        ]
                except Exception as e:
                    self.get_logger().debug(f'Read error: {e}')

        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now(). to_msg()
        msg.name = self.JOINT_NAMES
        msg.position = self. current_positions
        msg.velocity = [0.0] * 6
        msg.effort = [0.0] * 6
        
        self.joint_state_pub.publish(msg)

    def _gripper_callback(self, msg: Float64):
        """Handle gripper commands."""
        value = int(msg.data)
        
        with self.lock:
            if self.mc is not None:
                try:
                    if value <= 10:
                        # Close gripper
                        self.mc.set_gripper_state(1, 50)
                        self.get_logger().info('Gripper closed')
                    else:
                        # Open gripper
                        self.mc. set_gripper_state(0, 50)
                        self.get_logger().info('Gripper opened')
                except Exception as e:
                    self.get_logger().error(f'Gripper error: {e}')
            else:
                self.get_logger(). info(f'Gripper command: {value}')

    def _execute_trajectory_callback(self, goal_handle):
        """Execute received trajectory on robot hardware."""
        self. get_logger().info('Received trajectory goal')
        
        trajectory = goal_handle. request. trajectory
        result = FollowJointTrajectory.Result()
        
        if len(trajectory.points) == 0:
            self.get_logger(). warn('Empty trajectory received')
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result. INVALID_GOAL
            return result

        self.get_logger(). info(f'Executing {len(trajectory.points)} waypoints')
        
        start_time = time. time()
        
        for i, point in enumerate(trajectory.points):
            # Calculate wait time
            target_time = (
                point.time_from_start. sec + 
                point.time_from_start.nanosec * 1e-9
            )
            
            elapsed = time.time() - start_time
            wait_time = target_time - elapsed
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Convert radians to degrees for myCobot
            angles_deg = [math.degrees(p) for p in point. positions]
            
            # Calculate speed based on remaining time
            if i < len(trajectory.points) - 1:
                next_time = (
                    trajectory. points[i + 1].time_from_start.sec +
                    trajectory. points[i + 1].time_from_start.nanosec * 1e-9
                )
                segment_duration = next_time - target_time
                speed = min(100, max(10, int(100 / max(segment_duration, 0.5))))
            else:
                speed = 50

            with self.lock:
                if self.mc is not None:
                    try:
                        self.mc.send_angles(angles_deg, speed)
                        self.get_logger().info(
                            f'Point {i+1}/{len(trajectory.points)}: '
                            f'{[f"{a:.1f}" for a in angles_deg]}'
                        )
                    except Exception as e:
                        self.get_logger().error(f'Motion error: {e}')
                        goal_handle.abort()
                        result. error_code = FollowJointTrajectory.Result. PATH_TOLERANCE_VIOLATED
                        return result
                else:
                    self.get_logger().info(
                        f'[SIM] Point {i+1}: {[f"{a:.1f}" for a in angles_deg]}'
                    )
                    self.current_positions = list(point.positions)

        # Wait for motion to complete
        time.sleep(0.5)
        
        goal_handle.succeed()
        result. error_code = FollowJointTrajectory.Result. SUCCESSFUL
        self.get_logger(). info('Trajectory execution completed')
        
        return result


def main(args=None):
    rclpy.init(args=args)
    
    driver = MyCobotRobotDriver()
    
    executor = MultiThreadedExecutor(num_threads=4)
    executor. add_node(driver)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        driver.get_logger().error(f'Error: {e}')


if __name__ == '__main__':
    main()