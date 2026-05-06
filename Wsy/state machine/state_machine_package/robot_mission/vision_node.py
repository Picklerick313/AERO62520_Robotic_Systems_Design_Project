#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from robot_mission.srv import DetectBlock


class VisionNode(Node):
    """
    Minimal vision service node.

    Replace the mock string in handle_detect_block() with your real camera +
    color blob detection output.
    """
    def __init__(self):
        super().__init__("vision_node")
        self.service = self.create_service(
            DetectBlock,
            "vision_detect_block",
            self.handle_detect_block,
        )
        self.get_logger().info("vision_node ready: /vision_detect_block")

    def handle_detect_block(self, request, response):
        # request.mode can be:
        # - "search_block"
        # - "reachability"
        self.get_logger().info(f"Vision request mode: {request.mode}")

        response.success = True
        response.result_string = (
            "[mode=search_block] class=block:yellow | type=block | "
            "color=yellow | pos=(0.132, -0.001, 0.337) m | "
            "rz=35.3 deg | score=0.90"
        )
        return response


def main():
    rclpy.init()
    node = VisionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
