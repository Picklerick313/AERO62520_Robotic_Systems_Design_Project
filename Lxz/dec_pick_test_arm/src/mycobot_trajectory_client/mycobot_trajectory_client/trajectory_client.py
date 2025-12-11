#!/usr/bin/env python3
"""
Robot Hardware Interface - Runs on myCobot280Pi
Provides ros2_control interface for MoveIt2
This replaces direct pymycobot usage with ros2_control
"""

import math
from threading import Lock
import time

import rclpy
from rclpy. node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from sensor_msgs.msg import JointState
from std_msgs.msg import Header
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs. action import FollowJointTrajectory, GripperCommand
from rclpy.action import ActionServer

# Try to import pymycobot for hardware, but allow simulation
try:
    from pymycobot import MyCobot280
    HW_AVAILABLE = True
except ImportError:
    HW_AVAILABLE = False


class MyCobotHardwareInterface(Node):
    """
    Hardware interface node that bridges ros2_control to myCobot280Pi. 
    This runs on the robot and provides action servers for MoveIt2. 
    """
    
    JOINT_NAMES = [
        'joint2_to_joint1',
        'joint3_to_joint2',
        'joint4_to_joint3',
        'joint5_to_joint4',
        'joint6_to_joint5',
        'joint6output_to_joint6',
    ]
    
    def __init__(self):
        super().__init__('mycobot_hardware_interface')
        
        # Parameters
        self.declare_parameter('port', '/dev/ttyAMA0')
        self.declare_parameter('baud', 1000000)
        self.declare_parameter('simulate', not HW_AVAILABLE)
        
        port = self.get_parameter('port').value
        baud = self.get_parameter('baud').value
        self.simulate = self. get_parameter('simulate').value
        
        self.callback_group = ReentrantCallbackGroup()
        self.lock = Lock()
        
        # Current state
        self.current_positions = [0.0] * 6
        self.current_velocities = [0.0] * 6
        self.gripper_position = 0.0
        
        # Initialize hardware
        self.robot = None
        if not self.simulate and HW_AVAILABLE:
            try:
                self. robot = MyCobot280(port, baud)
                time.sleep(1.0)
                self.get_logger().info(f'Connected to myCobot on {port}')
            except Exception as e:
                self. get_logger().error(f'Hardware init failed: {e}')
                self. simulate = True
        
        if self.simulate:
            self.get_logger().warn('Running in SIMULATION mode')
        
        # Joint state publisher
        self.joint_state_pub = self.create_publisher(
            JointState, '/joint_states', 10
        )
        
        # Trajectory action server (for arm)
        self.trajectory_server = ActionServer(
            self,
            FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory',
            self._execute_trajectory,
            callback_group=self.callback_group
        )
        
        # Gripper action server
        self.gripper_server = ActionServer(
            self,
            GripperCommand,
            '/gripper_action_controller/gripper_cmd',
            self._execute_gripper,
            callback_group=self.callback_group
        )
        
        # Timer for publishing joint states
        self.create_timer(0.05, self._publish_joint_states)  # 20Hz
        
        self.get_logger(). info('myCobot Hardware Interface ready!')
    
    def _read_joint_positions(self) -> list:
        """Read current joint positions from hardware."""
        if self.simulate:
            return self.current_positions
        
        with self.lock:
            try:
                angles = self.robot. get_angles()
                if angles and len(angles) == 6:
                    return [math.radians(a) for a in angles]
            except:
                pass
        return self.current_positions
    
    def _publish_joint_states(self):
        """Publish current joint states."""
        positions = self._read_joint_positions()
        if positions:
            self.current_positions = positions
        
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now(). to_msg()
        msg.name = self.JOINT_NAMES
        msg.position = self.current_positions
        msg.velocity = self.current_velocities
        msg. effort = [0.0] * 6
        
        self.joint_state_pub.publish(msg)
    
    def _execute_trajectory(self, goal_handle):
        """Execute arm trajectory."""
        self.get_logger(). info('Executing trajectory.. .')
        
        trajectory = goal_handle.request. trajectory
        result = FollowJointTrajectory. Result()
        
        if len(trajectory.points) == 0:
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result. INVALID_GOAL
            return result
        
        # Execute each point
        for i, point in enumerate(trajectory.points):
            angles_deg = [math.degrees(p) for p in point.positions]
            
            self.get_logger(). info(
                f'Point {i+1}/{len(trajectory.points)}: '
                f'{[f"{a:.1f}" for a in angles_deg]}°'
            )
            
            if not self.simulate:
                with self.lock:
                    try:
                        self.robot.send_angles(angles_deg, 50)
                    except Exception as e:
                        self.get_logger().error(f'Motion error: {e}')
                        goal_handle.abort()
                        result. error_code = FollowJointTrajectory.Result. PATH_TOLERANCE_VIOLATED
                        return result
                
                # Wait for motion
                self._wait_for_position(point.positions, timeout=10.0)
            else:
                # Simulation: just update current positions
                self.current_positions = list(point.positions)
                time.sleep(1.0)
        
        goal_handle.succeed()
        result. error_code = FollowJointTrajectory.Result. SUCCESSFUL
        self.get_logger(). info('Trajectory completed!')
        return result
    
    def _wait_for_position(self, target_rad: list, timeout: float = 10.0):
        """Wait until robot reaches target position."""
        start = time.time()
        tolerance = math.radians(3.0)  # 3 degrees
        
        while (time.time() - start) < timeout:
            current = self._read_joint_positions()
            if current:
                errors = [abs(c - t) for c, t in zip(current, target_rad)]
                if max(errors) < tolerance:
                    return True
            time.sleep(0.1)
        return False
    
    def _execute_gripper(self, goal_handle):
        """Execute gripper command."""
        position = goal_handle. request.command. position
        
        self.get_logger(). info(f'Gripper command: position={position}')
        
        result = GripperCommand.Result()
        
        if not self.simulate:
            with self.lock:
                try:
                    if position < 0.1:
                        self.robot.set_gripper_state(1, 50)  # Close
                    else:
                        self. robot.set_gripper_state(0, 50)  # Open
                    time.sleep(1.5)
                except Exception as e:
                    self.get_logger().error(f'Gripper error: {e}')
                    goal_handle.abort()
                    return result
        else:
            self. gripper_position = position
            time.sleep(0.5)
        
        goal_handle.succeed()
        result.position = position
        result.reached_goal = True
        self.get_logger(). info('Gripper command completed')
        return result


def main(args=None):
    rclpy.init(args=args)
    
    node = MyCobotHardwareInterface()
    
    executor = MultiThreadedExecutor(num_threads=4)
    executor. add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        node.get_logger().error(f'Error: {e}')



if __name__ == '__main__':
    main()