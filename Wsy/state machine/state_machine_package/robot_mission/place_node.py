#!/usr/bin/env python3
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from robot_mission.action import PlaceBlock


class PlaceNode(Node):
    """
    Minimal place action server.

    Replace execute_callback() with bin detection + arm placing + gripper release.
    """
    def __init__(self):
        super().__init__("place_node")
        self.server = ActionServer(
            self,
            PlaceBlock,
            "place_block",
            self.execute_callback,
        )
        self.get_logger().info("place_node ready: /place_block")

    def execute_callback(self, goal_handle):
        self.get_logger().info(f"Place request for slot index: {goal_handle.request.slot_index}")

        feedback = PlaceBlock.Feedback()
        for p in [0.3, 0.6, 1.0]:
            feedback.progress = float(p)
            goal_handle.publish_feedback(feedback)
            time.sleep(0.2)

        goal_handle.succeed()
        result = PlaceBlock.Result()
        result.success = True
        result.message = "Mock place success."
        return result


def main():
    rclpy.init()
    node = PlaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
