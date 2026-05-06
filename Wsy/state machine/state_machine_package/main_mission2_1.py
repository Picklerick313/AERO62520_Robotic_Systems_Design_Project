#!/usr/bin/env python3
"""
main_mission2_1.py

A non-blocking ROS 2 state machine skeleton for mission 2.1.

This version finishes the original TODO-style placeholders and keeps the project
usable even before the real vision/arm/approach nodes are implemented.

Recommended node interfaces used by this file:
- Nav2 action:
    /navigate_to_pose                  nav2_msgs/action/NavigateToPose
- Search service:
    /search_object_service             robot_mission/srv/SearchTargets
- Vision service:
    /vision_detect_block               robot_mission/srv/DetectBlock
- Approach action:
    /approach_object_action            robot_mission/action/ApproachTarget
- Grasp action:
    /grasp_block                       robot_mission/action/GraspBlock
- Place action:
    /place_block                       robot_mission/action/PlaceBlock

If these custom interfaces are not built yet, set use_mock_modules=True in
RobotStateMachine() so the logic can still be tested.
"""

import math
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Point, PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from sensor_msgs.msg import LaserScan


# ---------------------------------------------------------------------------
# Optional custom interfaces.
# They are imported only if available. This lets the file run in mock mode
# before your .srv/.action files have been generated.
# ---------------------------------------------------------------------------
try:
    from robot_mission.srv import SearchTargets, DetectBlock
    from robot_mission.action import ApproachTarget, GraspBlock, PlaceBlock
    CUSTOM_INTERFACES_AVAILABLE = True
except Exception:
    SearchTargets = None
    DetectBlock = None
    ApproachTarget = None
    GraspBlock = None
    PlaceBlock = None
    CUSTOM_INTERFACES_AVAILABLE = False


class State(str, Enum):
    INIT = "INIT"
    IDLE = "IDLE"
    MAPPING = "MAPPING"
    SEARCH_OBJECT = "SEARCH_OBJECT"
    NAVIGATE_TO_OBJECT = "NAVIGATE_TO_OBJECT"
    GRASP_OBJECT = "GRASP_OBJECT"
    RETRY_TEST = "RETRY_TEST"
    NAVIGATE_TO_BIN = "NAVIGATE_TO_BIN"
    PLACE_OBJECT = "PLACE_OBJECT"
    RECOVERY = "RECOVERY"
    DONE = "DONE"


@dataclass
class Target:
    x: float
    y: float
    z: float = 0.0


def yaw_to_quaternion(yaw: float):
    """Return a geometry_msgs Quaternion represented through Pose orientation fields."""
    z = math.sin(yaw / 2.0)
    w = math.cos(yaw / 2.0)
    return z, w


class RobotStateMachine:
    def __init__(self, use_mock_modules: bool = False):
        self.state = State.INIT
        self.node: Optional[Node] = None
        self.use_mock_modules = use_mock_modules or (not CUSTOM_INTERFACES_AVAILABLE)

        # Mission counters
        self.max_blocks = 3
        self.total_count = 0
        self.success_count = 0
        self.fail_count = 0

        self.succeed_place_count = 0
        self.total_place_count = 0
        self.fail_place_count = 0

        # Mapping and target storage
        self.mapping_duration = 120.0
        self.mapping_start_time: Optional[float] = None
        self.potential_targets: List[Dict[str, float]] = []
        self._last_lidar_save_time = 0.0

        # Navigation / action state
        self.is_navigating = False
        self.nav_done = False
        self.nav_success = False
        self.nav_start_time: Optional[float] = None
        self.navigation_timeout = 45.0

        self.is_returning = False
        self.return_done = False
        self.return_success = False

        # Search state
        self.is_searching = False
        self.search_future = None

        # Vision / grasp state
        self.is_vision_requested = False
        self.vision_future = None
        self.current_target_block: Optional[Dict[str, float]] = None

        self.is_grasp_requested = False
        self.grasp_done = False
        self.grasp_success = False
        self._grasp_goal_sent = False

        # Reachability state
        self.is_reachability_requested = False
        self.reachability_future = None
        self.camera_aligned_for_bin = False

        # Place state
        self.is_place_requested = False
        self.place_done = False
        self.place_success = False
        self._place_goal_sent = False

        # Return-to-start state
        self.start_pose = Target(0.0, 0.0, 0.0)
        self.bin_pose = Target(0.0, 0.0, 0.0)

        # ROS handles
        self.nav_client = None
        self.search_client = None
        self.vision_client = None
        self.maps_to_object_client = None
        self.grasp_client = None
        self.place_client = None
        self.cmd_vel_pub = None
        self.lidar_sub = None

        self.explore_goal_future = None
        self.explore_result_future = None
        self.explore_goal_handle = None

        self.return_goal_future = None
        self.return_result_future = None
        self.return_goal_handle = None

    # ------------------------------------------------------------------
    # ROS setup
    # ------------------------------------------------------------------
    def init_communications(self) -> bool:
        try:
            if not rclpy.ok():
                rclpy.init()

            self.node = rclpy.create_node("robot_state_machine_node")
            self.node.get_logger().info("ROS 2 State Machine Node initialized.")

            self.nav_client = ActionClient(self.node, NavigateToPose, "navigate_to_pose")
            self.node.get_logger().info("Waiting for Nav2 action server /navigate_to_pose ...")
            if not self.nav_client.wait_for_server(timeout_sec=5.0):
                self.node.get_logger().error("Nav2 server timeout. Is Nav2 running?")
                return False

            self.cmd_vel_pub = self.node.create_publisher(Twist, "/cmd_vel", 10)

            self.lidar_sub = self.node.create_subscription(
                LaserScan,
                "/scan",
                self.lidar_callback,
                10,
            )

            if self.use_mock_modules:
                self.node.get_logger().warn(
                    "Running in mock mode. Search/Vision/Approach/Grasp/Place are simulated."
                )
                return True

            self.search_client = self.node.create_client(SearchTargets, "search_object_service")
            self.vision_client = self.node.create_client(DetectBlock, "vision_detect_block")
            self.maps_to_object_client = ActionClient(
                self.node, ApproachTarget, "approach_object_action"
            )
            self.grasp_client = ActionClient(self.node, GraspBlock, "grasp_block")
            self.place_client = ActionClient(self.node, PlaceBlock, "place_block")

            self.node.get_logger().info("Custom mission clients initialized.")
            return True

        except Exception as e:
            print(f"Failed to initialize ROS 2 communications: {e}")
            return False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        if not rclpy.ok():
            rclpy.init()    
            
        while self.state != State.DONE and rclpy.ok():
            if self.node:
                rclpy.spin_once(self.node, timeout_sec=0.1)

            if self.state == State.INIT:
                print("System Initializing...")
                self.state = State.IDLE if self.init_communications() else State.RECOVERY

            elif self.state == State.IDLE:
                self.node.get_logger().info("Idle. Transitioning to MAPPING.")
                self.state = State.MAPPING

            elif self.state == State.MAPPING:
                self.handle_mapping_state()

            elif self.state == State.SEARCH_OBJECT:
                if self.check_if_stuck():
                    self.state = State.RECOVERY
                    continue

                target_found = self.execute_search()
                if target_found is True:
                    self.node.get_logger().info("Target found. Transitioning to NAVIGATE_TO_OBJECT.")
                    self.state = State.NAVIGATE_TO_OBJECT
                elif target_found is False:
                    self.node.get_logger().warn("No target found. Retrying search.")
                    self.reset_search_state()

            elif self.state == State.NAVIGATE_TO_OBJECT:
                if self.check_if_stuck():
                    self.state = State.RECOVERY
                    continue

                reached_position = self.navigate_to_target()
                if reached_position is True:
                    self.node.get_logger().info("Reached grasp position.")
                    self.state = State.GRASP_OBJECT
                elif reached_position is False and self.nav_done:
                    self.state = State.SEARCH_OBJECT

            elif self.state == State.GRASP_OBJECT:
                if self.fail_count >= 3:
                    self.node.get_logger().warn("Failed grasping 3 times. Recovery required.")
                    self.state = State.RECOVERY
                    continue

                grasp_result = self.execute_grasp()
                if grasp_result is True:
                    self.total_count += 1
                    self.success_count += 1
                    self.node.get_logger().info(
                        f"Grasp success. Collected blocks: {self.total_count}/{self.max_blocks}"
                    )
                    self.reset_grasp_state()
                    self.state = State.NAVIGATE_TO_BIN if self.total_count >= self.max_blocks else State.SEARCH_OBJECT

                elif grasp_result is False:
                    self.node.get_logger().warn("Grasp failed or no target. Transitioning to RETRY_TEST.")
                    self.reset_grasp_state(keep_target=True)
                    self.state = State.RETRY_TEST

            elif self.state == State.RETRY_TEST:
                if not self.align_camera_for_bin_surface():
                    self.state = State.RECOVERY
                    continue

                is_within_reach = self.check_reachability()
                if is_within_reach is True:
                    self.node.get_logger().info("Object is still reachable. Retrying grasp.")
                    self.reset_reachability_state()
                    self.state = State.GRASP_OBJECT

                elif is_within_reach is False:
                    self.node.get_logger().warn("Object is not reachable. Aborting this block.")
                    self.total_count += 1
                    self.fail_count += 1
                    self.reset_reachability_state()
                    self.state = State.NAVIGATE_TO_BIN if self.total_count >= self.max_blocks else State.SEARCH_OBJECT

            elif self.state == State.NAVIGATE_TO_BIN:
                if self.check_if_stuck():
                    self.state = State.RECOVERY
                    continue

                nav_bin_result = self.navigate_to_bin_location()
                if nav_bin_result is True:
                    self.node.get_logger().info("Returned to bin area.")
                    self.state = State.PLACE_OBJECT
                elif nav_bin_result is False:
                    self.node.get_logger().error("Failed to navigate to bin.")
                    self.state = State.RECOVERY

            elif self.state == State.PLACE_OBJECT:
                if self.fail_place_count >= 3:
                    self.node.get_logger().error("Failed placing 3 times. Recovery required.")
                    self.state = State.RECOVERY
                    continue

                place_result = self.execute_place()
                if place_result is True:
                    self.succeed_place_count += 1
                    self.total_place_count += 1
                    self.node.get_logger().info(
                        f"Place success. Placed: {self.succeed_place_count}/{self.success_count}"
                    )
                    self.reset_place_state()

                    if self.succeed_place_count >= self.success_count:
                        self.node.get_logger().info("All carried objects placed. Going back to start.")
                        self.go_back_to_starting_point()
                        self.state = State.DONE
                    else:
                        self.state = State.PLACE_OBJECT

                elif place_result is False:
                    self.fail_place_count += 1
                    self.total_place_count += 1
                    self.reset_place_state()
                    self.state = State.PLACE_OBJECT

            elif self.state == State.RECOVERY:
                self.node.get_logger().fatal("Robot stuck or error limit reached.")
                self.request_human_intervention()
                self.state = State.DONE

        if self.node:
            self.node.get_logger().info("State Machine shutting down.")
            self.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------
    def handle_mapping_state(self):
        if self.mapping_start_time is None:
            self.node.get_logger().info(f"MAPPING started. Time limit: {self.mapping_duration}s")
            self.mapping_start_time = time.time()
            self.start_exploring()

        elapsed_time = time.time() - self.mapping_start_time
        if elapsed_time >= self.mapping_duration:
            self.node.get_logger().info(
                f"Mapping complete. Stored {len(self.potential_targets)} potential target signatures."
            )
            self.stop_exploring()
            self.mapping_start_time = None
            self.state = State.SEARCH_OBJECT

    # ------------------------------------------------------------------
    # LIDAR target storage
    # ------------------------------------------------------------------
    def lidar_callback(self, msg: LaserScan):
        if self.state not in [State.MAPPING, State.SEARCH_OBJECT]:
            return

        if not msg.intensities:
            self.node.get_logger().warn(
                "LIDAR does not output intensity. White-bin detection disabled.",
                throttle_duration_sec=5.0,
            )
            return

        intensity_threshold = 8000
        now = time.time()

        for i, intensity in enumerate(msg.intensities):
            if intensity <= intensity_threshold:
                continue

            distance = msg.ranges[i]
            if not math.isfinite(distance) or not (0.2 < distance < msg.range_max):
                continue

            angle = msg.angle_min + i * msg.angle_increment

            # Avoid saving hundreds of points from the same reflective surface.
            if now - self._last_lidar_save_time < 0.5:
                continue

            target_info = {"angle": float(angle), "distance": float(distance)}
            if not self.is_duplicate_polar_target(target_info):
                self.potential_targets.append(target_info)
                self._last_lidar_save_time = now
                self.node.get_logger().info(
                    f"Stored reflective candidate: angle={angle:.2f}, distance={distance:.2f}"
                )

    def is_duplicate_polar_target(self, new_target: Dict[str, float]) -> bool:
        for target in self.potential_targets:
            if "angle" not in target or "distance" not in target:
                continue
            if (
                abs(target["angle"] - new_target["angle"]) < 0.08
                and abs(target["distance"] - new_target["distance"]) < 0.25
            ):
                return True
        return False

    # ------------------------------------------------------------------
    # Exploring with Nav2
    # ------------------------------------------------------------------
    def start_exploring(self):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = 2.0
        goal_msg.pose.pose.position.y = 2.0
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.w = 1.0

        self.node.get_logger().info("Sending exploration goal to Nav2.")
        self.explore_goal_future = self.nav_client.send_goal_async(goal_msg)
        self.explore_goal_future.add_done_callback(self.explore_goal_response_callback)

    def explore_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node.get_logger().error("Exploration goal was rejected by Nav2.")
            return

        self.explore_goal_handle = goal_handle
        self.node.get_logger().info("Exploration goal accepted.")
        self.explore_result_future = goal_handle.get_result_async()
        self.explore_result_future.add_done_callback(self.explore_result_callback)

    def explore_result_callback(self, future):
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.node.get_logger().info("Exploration goal reached.")
        else:
            self.node.get_logger().warn(f"Exploration finished with status: {status}")

    def stop_exploring(self):
        self.node.get_logger().info("Stopping exploration.")
        self.publish_stop()
        if self.explore_goal_handle is not None:
            self.explore_goal_handle.cancel_goal_async()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def execute_search(self):
        if self.use_mock_modules:
            if not self.potential_targets:
                self.potential_targets = [{"x": 1.0, "y": 0.5}]
            return True

        if not self.is_searching:
            if self.search_client is None:
                self.node.get_logger().error("Search client is not configured.")
                return False

            if not self.search_client.service_is_ready():
                self.node.get_logger().warn("Search service not ready.", throttle_duration_sec=2.0)
                return None

            request = SearchTargets.Request()
            self.search_future = self.search_client.call_async(request)
            self.is_searching = True
            return None

        if self.search_future.done():
            self.is_searching = False
            try:
                response = self.search_future.result()
            except Exception as e:
                self.node.get_logger().error(f"Search service call failed: {e}")
                return False

            if response.success and len(response.targets) > 0:
                self.potential_targets.clear()
                for pt in response.targets:
                    self.potential_targets.append({"x": pt.x, "y": pt.y, "z": pt.z})
                return True

            return False

        return None

    # ------------------------------------------------------------------
    # Navigate to object
    # ------------------------------------------------------------------
    def navigate_to_target(self):
        if self.use_mock_modules:
            time.sleep(0.2)
            self.nav_done = True
            self.nav_success = True
            return True

        if not self.is_navigating:
            if self.maps_to_object_client is None:
                self.node.get_logger().error("Approach action client is not configured.")
                self.nav_done = True
                self.nav_success = False
                return False

            if not self.maps_to_object_client.server_is_ready():
                self.node.get_logger().warn("Approach action server not ready.", throttle_duration_sec=2.0)
                return None

            if not self.potential_targets:
                self.node.get_logger().warn("No target candidate to approach.")
                self.nav_done = True
                self.nav_success = False
                return False

            goal_msg = ApproachTarget.Goal()
            for pt_dict in self.potential_targets:
                ros_point = Point()
                ros_point.x = float(pt_dict.get("x", 0.0))
                ros_point.y = float(pt_dict.get("y", 0.0))
                ros_point.z = float(pt_dict.get("z", 0.0))
                goal_msg.targets.append(ros_point)

            self.node.get_logger().info(f"Sending {len(goal_msg.targets)} target candidates to approach node.")
            self.is_navigating = True
            self.nav_done = False
            self.nav_success = False
            self.nav_start_time = time.time()

            self.approach_goal_future = self.maps_to_object_client.send_goal_async(
                goal_msg,
                feedback_callback=self.nav_feedback_callback,
            )
            self.approach_goal_future.add_done_callback(self.approach_goal_response_callback)
            return None

        if self.nav_done:
            self.is_navigating = False
            self.nav_start_time = None
            return self.nav_success

        return None

    def approach_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node.get_logger().error("Approach node rejected the request.")
            self.nav_done = True
            self.nav_success = False
            return

        self.node.get_logger().info("Approach request accepted.")
        self.approach_result_future = goal_handle.get_result_async()
        self.approach_result_future.add_done_callback(self.approach_get_result_callback)

    def approach_get_result_callback(self, future):
        result_wrapper = future.result()
        result = result_wrapper.result
        status = result_wrapper.status

        self.nav_success = bool(status == GoalStatus.STATUS_SUCCEEDED and result.success)
        self.nav_done = True

    def nav_feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        if hasattr(feedback, "distance_remaining"):
            self.node.get_logger().info(
                f"Approach distance remaining: {feedback.distance_remaining:.2f} m",
                throttle_duration_sec=1.0,
            )

    # ------------------------------------------------------------------
    # Grasp
    # ------------------------------------------------------------------
    def execute_grasp(self):
        if self.use_mock_modules:
            self.current_target_block = {
                "color": "yellow",
                "x": 0.13,
                "y": 0.00,
                "z": 0.34,
                "rz": 35.0,
            }
            return True

        if not self.is_vision_requested and not self.is_grasp_requested:
            if self.vision_client is None:
                self.node.get_logger().error("Vision client is not configured.")
                return False

            if not self.vision_client.service_is_ready():
                self.node.get_logger().warn("Vision service not ready.", throttle_duration_sec=2.0)
                return None

            request = DetectBlock.Request()
            request.mode = "search_block"
            self.vision_future = self.vision_client.call_async(request)
            self.is_vision_requested = True
            return None

        if self.is_vision_requested and not self.is_grasp_requested:
            if not self.vision_future.done():
                return None

            self.is_vision_requested = False
            try:
                response = self.vision_future.result()
                vision_text = response.result_string
            except Exception as e:
                self.node.get_logger().error(f"Vision service call failed: {e}")
                return False

            parsed = self.parse_vision_text(vision_text)
            if parsed is None:
                return False

            self.current_target_block = parsed
            self.is_grasp_requested = True
            self.grasp_done = False
            self.grasp_success = False
            self._grasp_goal_sent = False
            return None

        if self.is_grasp_requested and not self.grasp_done:
            if self.grasp_client is None:
                self.node.get_logger().error("Grasp action client is not configured.")
                return False

            if not self.grasp_client.server_is_ready():
                self.node.get_logger().warn("Grasp action server not ready.", throttle_duration_sec=2.0)
                return None

            if not self._grasp_goal_sent:
                goal_msg = GraspBlock.Goal()
                goal_msg.color = str(self.current_target_block["color"])
                goal_msg.target.x = float(self.current_target_block["x"])
                goal_msg.target.y = float(self.current_target_block["y"])
                goal_msg.target.z = float(self.current_target_block["z"])
                goal_msg.rz = float(self.current_target_block["rz"])

                self.grasp_goal_future = self.grasp_client.send_goal_async(goal_msg)
                self.grasp_goal_future.add_done_callback(self.grasp_goal_response_callback)
                self._grasp_goal_sent = True

            return None

        if self.is_grasp_requested and self.grasp_done:
            return self.grasp_success

        return None

    def grasp_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node.get_logger().error("Grasp node rejected the request.")
            self.grasp_done = True
            self.grasp_success = False
            return

        self.node.get_logger().info("Grasp request accepted.")
        self.grasp_result_future = goal_handle.get_result_async()
        self.grasp_result_future.add_done_callback(self.grasp_get_result_callback)

    def grasp_get_result_callback(self, future):
        result_wrapper = future.result()
        result = result_wrapper.result
        status = result_wrapper.status

        self.grasp_success = bool(status == GoalStatus.STATUS_SUCCEEDED and result.success)
        self.grasp_done = True

    # ------------------------------------------------------------------
    # Retry reachability
    # ------------------------------------------------------------------
    def align_camera_for_bin_surface(self) -> bool:
        if self.camera_aligned_for_bin:
            return True

        self.node.get_logger().info("Aligning camera for retry inspection.")
        # TODO: replace this with a real servo/gimbal call if your hardware has one.
        self.camera_aligned_for_bin = True
        return True

    def check_reachability(self):
        if self.use_mock_modules:
            return True

        if not self.is_reachability_requested:
            if self.vision_client is None:
                self.node.get_logger().error("Vision client is not configured.")
                return False

            if not self.vision_client.service_is_ready():
                self.node.get_logger().warn("Vision service not ready.", throttle_duration_sec=2.0)
                return None

            request = DetectBlock.Request()
            request.mode = "reachability"
            self.reachability_future = self.vision_client.call_async(request)
            self.is_reachability_requested = True
            return None

        if not self.reachability_future.done():
            return None

        self.is_reachability_requested = False
        try:
            response = self.reachability_future.result()
            vision_text = response.result_string
        except Exception as e:
            self.node.get_logger().error(f"Reachability vision call failed: {e}")
            return False

        parsed = self.parse_vision_text(vision_text)
        if parsed is None:
            return False

        z_threshold = -0.02
        if parsed["z"] >= z_threshold:
            self.current_target_block = parsed
            return True

        return False

    # ------------------------------------------------------------------
    # Navigate to bin/start using Nav2
    # ------------------------------------------------------------------
    def navigate_to_bin_location(self):
        return self.navigate_to_fixed_pose(
            self.bin_pose.x,
            self.bin_pose.y,
            0.0,
            state_flag_name="is_returning",
            done_flag_name="return_done",
            success_flag_name="return_success",
        )

    def go_back_to_starting_point(self):
        result = None
        while rclpy.ok() and result is not True:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            result = self.navigate_to_fixed_pose(
                self.start_pose.x,
                self.start_pose.y,
                0.0,
                state_flag_name="is_returning",
                done_flag_name="return_done",
                success_flag_name="return_success",
            )
            if result is False:
                self.node.get_logger().error("Failed to go back to starting point.")
                return False
        return True

    def navigate_to_fixed_pose(
        self,
        x: float,
        y: float,
        yaw: float,
        state_flag_name: str,
        done_flag_name: str,
        success_flag_name: str,
    ):
        if self.use_mock_modules:
            time.sleep(0.2)
            return True

        is_active = getattr(self, state_flag_name)
        is_done = getattr(self, done_flag_name)
        is_success = getattr(self, success_flag_name)

        if not is_active:
            goal_msg = NavigateToPose.Goal()
            goal_msg.pose.header.frame_id = "map"
            goal_msg.pose.header.stamp = self.node.get_clock().now().to_msg()
            goal_msg.pose.pose.position.x = float(x)
            goal_msg.pose.pose.position.y = float(y)
            goal_msg.pose.pose.position.z = 0.0
            qz, qw = yaw_to_quaternion(yaw)
            goal_msg.pose.pose.orientation.z = qz
            goal_msg.pose.pose.orientation.w = qw

            self.return_goal_future = self.nav_client.send_goal_async(goal_msg)
            self.return_goal_future.add_done_callback(
                lambda future: self.fixed_pose_goal_response_callback(
                    future, done_flag_name, success_flag_name
                )
            )

            setattr(self, state_flag_name, True)
            setattr(self, done_flag_name, False)
            setattr(self, success_flag_name, False)
            self.nav_start_time = time.time()
            return None

        if is_done:
            setattr(self, state_flag_name, False)
            self.nav_start_time = None
            return bool(is_success)

        return None

    def fixed_pose_goal_response_callback(self, future, done_flag_name: str, success_flag_name: str):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node.get_logger().error("Fixed-pose Nav2 goal was rejected.")
            setattr(self, done_flag_name, True)
            setattr(self, success_flag_name, False)
            return

        self.return_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda result_future_: self.fixed_pose_result_callback(
                result_future_, done_flag_name, success_flag_name
            )
        )

    def fixed_pose_result_callback(self, future, done_flag_name: str, success_flag_name: str):
        status = future.result().status
        setattr(self, success_flag_name, status == GoalStatus.STATUS_SUCCEEDED)
        setattr(self, done_flag_name, True)

    # ------------------------------------------------------------------
    # Place
    # ------------------------------------------------------------------
    def execute_place(self):
        if self.use_mock_modules:
            time.sleep(0.2)
            return True

        if not self.is_place_requested:
            if self.place_client is None:
                self.node.get_logger().error("Place action client is not configured.")
                return False

            if not self.place_client.server_is_ready():
                self.node.get_logger().warn("Place action server not ready.", throttle_duration_sec=2.0)
                return None

            goal_msg = PlaceBlock.Goal()
            goal_msg.slot_index = int(self.succeed_place_count)

            self.place_goal_future = self.place_client.send_goal_async(goal_msg)
            self.place_goal_future.add_done_callback(self.place_goal_response_callback)

            self.is_place_requested = True
            self.place_done = False
            self.place_success = False
            self._place_goal_sent = True
            return None

        if self.place_done:
            return self.place_success

        return None

    def place_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node.get_logger().error("Place node rejected the request.")
            self.place_done = True
            self.place_success = False
            return

        self.node.get_logger().info("Place request accepted.")
        self.place_result_future = goal_handle.get_result_async()
        self.place_result_future.add_done_callback(self.place_get_result_callback)

    def place_get_result_callback(self, future):
        result_wrapper = future.result()
        result = result_wrapper.result
        status = result_wrapper.status

        self.place_success = bool(status == GoalStatus.STATUS_SUCCEEDED and result.success)
        self.place_done = True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def parse_vision_text(self, vision_text: str):
        if not vision_text or "No Target" in vision_text:
            self.node.get_logger().warn("Vision reports no target.")
            return None

        try:
            color_match = re.search(r"color=(\w+)", vision_text)
            color = color_match.group(1) if color_match else "unknown"

            pos_match = re.search(r"pos=\(([^,]+),\s*([^,]+),\s*([^)]+)\)", vision_text)
            if not pos_match:
                self.node.get_logger().error(f"Cannot parse position from: {vision_text}")
                return None

            rz_match = re.search(r"rz=([-\d.]+)", vision_text)
            rz = float(rz_match.group(1)) if rz_match else 0.0

            return {
                "color": color,
                "x": float(pos_match.group(1)),
                "y": float(pos_match.group(2)),
                "z": float(pos_match.group(3)),
                "rz": rz,
            }
        except Exception as e:
            self.node.get_logger().error(f"Vision parse failed: {e}. Raw: {vision_text}")
            return None

    def check_if_stuck(self) -> bool:
        if self.nav_start_time and (time.time() - self.nav_start_time > self.navigation_timeout):
            self.node.get_logger().error("Navigation timeout. Robot may be stuck.")
            self.publish_stop()
            self.is_navigating = False
            self.is_returning = False
            return True
        return False

    def publish_stop(self):
        if self.cmd_vel_pub is None:
            return
        self.cmd_vel_pub.publish(Twist())

    def reset_search_state(self):
        self.is_searching = False
        self.search_future = None

    def reset_grasp_state(self, keep_target: bool = False):
        self.is_vision_requested = False
        self.vision_future = None
        self.is_grasp_requested = False
        self.grasp_done = False
        self.grasp_success = False
        self._grasp_goal_sent = False
        self.camera_aligned_for_bin = False
        if not keep_target:
            self.current_target_block = None

    def reset_reachability_state(self):
        self.is_reachability_requested = False
        self.reachability_future = None
        self.camera_aligned_for_bin = False

    def reset_place_state(self):
        self.is_place_requested = False
        self.place_done = False
        self.place_success = False
        self._place_goal_sent = False

    def request_human_intervention(self):
        if self.node:
            self.node.get_logger().error("Recovery requires human intervention.")
            self.node.get_logger().error("Plan A: reset robot/blocks, then restart mission.")
            self.node.get_logger().error("Plan B: manually place remaining blocks into the carrier.")


def main():
    print("===== main_mission2_1.py started =====", flush=True)

    sm = RobotStateMachine(use_mock_modules=False)

    print("===== RobotStateMachine created =====", flush=True)

    sm.run()

    print("===== State machine finished =====", flush=True)


if __name__ == "__main__":
    print("===== __main__ entered =====", flush=True)
    main()
