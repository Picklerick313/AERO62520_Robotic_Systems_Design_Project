#!/usr/bin/env python3
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from robot_mission.action import ApproachTarget


class ApproachObjectNode(Node):
    """
    Minimal approach action server.

    Replace execute_callback() with:
    1. choose the best target candidate,
    2. send Nav2 goal near the object,
    3. perform local alignment,
    4. stop around 0.8 m away from the object.
    """
    def __init__(self):
        super().__init__("approach_object_node")
        self.server = ActionServer(
            self,
            ApproachTarget,
            "approach_object_action",
            self.execute_callback,
        )
        self.get_logger().info("approach_object_node ready: /approach_object_action")

    def execute_callback(self, goal_handle):
        self.get_logger().info(f"Received {len(goal_handle.request.targets)} target candidates.")

        feedback = ApproachTarget.Feedback()
        for d in [1.5, 1.2, 1.0, 0.8]:
            feedback.distance_remaining = float(d)
            goal_handle.publish_feedback(feedback)
            time.sleep(0.2)

        goal_handle.succeed()
        result = ApproachTarget.Result()
        result.success = True
        result.message = "Mock approach finished at grasp distance."
        return result


def main():
    rclpy.init()
    node = ApproachObjectNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
