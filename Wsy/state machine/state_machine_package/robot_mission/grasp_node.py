#!/usr/bin/env python3
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from robot_mission.action import GraspBlock


class GraspNode(Node):
    """
    Minimal grasp action server.

    Replace execute_callback() with your real arm IK / servo / gripper sequence.
    """
    def __init__(self):
        super().__init__("grasp_node")
        self.server = ActionServer(
            self,
            GraspBlock,
            "grasp_block",
            self.execute_callback,
        )
        self.get_logger().info("grasp_node ready: /grasp_block")

    def execute_callback(self, goal_handle):
        req = goal_handle.request
        self.get_logger().info(
            f"Grasp request: color={req.color}, "
            f"pos=({req.target.x:.3f}, {req.target.y:.3f}, {req.target.z:.3f}), rz={req.rz:.1f}"
        )

        feedback = GraspBlock.Feedback()
        for p in [0.25, 0.50, 0.75, 1.00]:
            feedback.progress = float(p)
            goal_handle.publish_feedback(feedback)
            time.sleep(0.2)

        goal_handle.succeed()
        result = GraspBlock.Result()
        result.success = True
        result.message = "Mock grasp success."
        return result


def main():
    rclpy.init()
    node = GraspNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
