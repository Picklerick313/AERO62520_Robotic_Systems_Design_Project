#!/usr/bin/env python3
import rclpy
from rclpy. node import Node
from example_interfaces.srv import Trigger
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class GraspServer(Node):
    def __init__(self):
        super().__init__('grasp_server')
        self.srv = self.create_service(Trigger, 'execute_grasp', self.execute_grasp_callback)
        self.traj_pub = self.create_publisher(JointTrajectory, 'joint_trajectory', 10)
        self.get_logger().info('Grasp server ready')

    def execute_grasp_callback(self, request, response):
        # Send trajectory: approach, grasp, lift
        traj = JointTrajectory()
        traj.joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'gripper']
        
        # Approach position
        pt1 = JointTrajectoryPoint()
        pt1.positions = [0.0, -0.5, 1.0, 0.0, 0.5, 0.0, 0.05]
        pt1.time_from_start. sec = 2
        
        # Grasp position (close gripper)
        pt2 = JointTrajectoryPoint()
        pt2.positions = [0.0, -0.5, 1.0, 0.0, 0.5, 0.0, 0.0]
        pt2.time_from_start.sec = 4
        
        # Release position
        pt3 = JointTrajectoryPoint()
        pt3.positions = [0.5, -0.3, 0.8, 0.0, 0.3, 0.0, 0.05]
        pt3.time_from_start.sec = 6
        
        traj.points = [pt1, pt2, pt3]
        self.traj_pub.publish(traj)
        
        response.success = True
        response. message = 'Trajectory sent'
        return response

def main():
    rclpy.init()
    node = GraspServer()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()