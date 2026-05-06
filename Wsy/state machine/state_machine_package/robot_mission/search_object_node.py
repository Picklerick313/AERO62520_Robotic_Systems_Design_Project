#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point

from robot_mission.srv import SearchTargets


class SearchObjectNode(Node):
    """
    Minimal target search service.

    Later, replace the fixed target with clustered output from map/LIDAR/vision.
    """
    def __init__(self):
        super().__init__("search_object_node")
        self.service = self.create_service(
            SearchTargets,
            "search_object_service",
            self.handle_search,
        )
        self.get_logger().info("search_object_node ready: /search_object_service")

    def handle_search(self, request, response):
        pt = Point()
        pt.x = 1.0
        pt.y = 0.5
        pt.z = 0.0

        response.success = True
        response.targets = [pt]
        response.message = "Mock target returned."
        return response


def main():
    rclpy.init()
    node = SearchObjectNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
