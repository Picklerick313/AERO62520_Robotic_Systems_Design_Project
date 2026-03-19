#!/usr/bin/env python3
import math, asyncio, concurrent.futures, sys, pathlib
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory, GripperCommand
from pymycobot import MyCobot280, utils as mc_utils

JOINTS = [
    "link1_to_link2", "link2_to_link3", "link3_to_link4",
    "link4_to_link5", "link5_to_link6", "link6_to_link6_flange"
]
GRIPPER = "gripper_controller"

def rad2deg_list(rad_list): return [math.degrees(r) for r in rad_list]
def clamp_speed(speed): return max(1, min(int(speed), 100))

def choose_port(requested: str):
    ports = mc_utils.get_port_list() or []
    if pathlib.Path(requested).exists():
        return requested, ports
    for cand in ["/dev/ttyAMA0", "/dev/ttyUSB0", "/dev/ttyACM0"]:
        if pathlib.Path(cand).exists():
            return cand, ports
    return None, ports

class MyCobotDriver(Node):
    def __init__(self):
        super().__init__("pymycobot_driver")
        req_port = self.declare_parameter("port", "/dev/ttyAMA0").get_parameter_value().string_value
        baud     = self.declare_parameter("baud", 1000000).get_parameter_value().integer_value
        self.speed = clamp_speed(self.declare_parameter("speed", 40).get_parameter_value().integer_value)

        port, ports_seen = choose_port(req_port)
        if port is None:
            self.get_logger().error(f"Port {req_port} not found. Available: {ports_seen or 'none'}")
            raise RuntimeError(f"Missing serial port {req_port}")
        if port != req_port:
            self.get_logger().warn(f"Requested {req_port} missing; using {port} instead")

        self.mc = MyCobot280(port, baud)
        self.mc.power_on()
        self.mc.clear_error_information()

        # use a separate thread pool; do NOT name it executor
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.js_pub = self.create_publisher(JointState, "joint_states", 10)
        self.create_timer(0.05, self.publish_js)

        self.arm_as = ActionServer(self, FollowJointTrajectory,
                                   "arm_controller/follow_joint_trajectory",
                                   execute_callback=self.execute_arm)
        self.grip_as = ActionServer(self, GripperCommand,
                                    "gripper_action",
                                    execute_callback=self.execute_grip)

    def publish_js(self):
        try:
            angles = self.mc.get_angles()
            if not angles or len(angles) < 6:
                return
            grip_raw = self.mc.get_gripper_value() or 0
            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.name = JOINTS + [GRIPPER]
            msg.position = [math.radians(a) for a in angles] + [grip_raw/1000.0]
            self.js_pub.publish(msg)
        except Exception as e:
            self.get_logger().warn(f"JS publish error: {e}")

    async def execute_arm(self, goal_handle):
        traj = goal_handle.request.trajectory
        for pt in traj.points:
            target_deg = rad2deg_list(pt.positions[:6])
            t = pt.time_from_start.sec + pt.time_from_start.nanosec*1e-9
            await self.async_call(self.mc.sync_send_angles, target_deg, self.speed, max(t, 3))
        goal_handle.succeed()
        return FollowJointTrajectory.Result()

    async def execute_grip(self, goal_handle):
        pos_m = goal_handle.request.command.position
        target = max(0, min(int(pos_m * 1000 / 0.01), 100))
        await self.async_call(self.mc.set_gripper_value, target, 70)
        goal_handle.succeed()
        res = GripperCommand.Result()
        res.position = pos_m
        res.reached_goal = True
        return res

    async def async_call(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.pool, lambda: func(*args))

def main():
    try:
        rclpy.init()
        node = MyCobotDriver()
    except Exception as e:
        rclpy.logging.get_logger("pymycobot_driver").error(f"Driver failed: {e}")
        raise e
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        pass


if __name__ == "__main__":
    main()