#!/usr/bin/env python3
import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def read_yaml(path: str):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data if data is not None else {}


def read_text(path: str):
    with open(path, "r") as f:
        return f.read()


def require_file(path: str, label: str):
    if not os.path.exists(path):
        raise RuntimeError(f"[move_group.launch.py] Missing {label}: {path}")


def launch_setup(context, *args, **kwargs):
    model = LaunchConfiguration("model").perform(context)
    srdf = LaunchConfiguration("srdf").perform(context)
    kinematics = LaunchConfiguration("kinematics").perform(context)
    joint_limits = LaunchConfiguration("joint_limits").perform(context)
    ompl = LaunchConfiguration("ompl").perform(context)
    controllers = LaunchConfiguration("controllers").perform(context)
    rviz_config = LaunchConfiguration("rviz_config").perform(context)

    use_rviz = LaunchConfiguration("use_rviz")
    use_sim_time = LaunchConfiguration("use_sim_time")

    require_file(model, "URDF/Xacro model")
    require_file(srdf, "SRDF")
    require_file(kinematics, "kinematics.yaml")
    require_file(joint_limits, "joint_limits.yaml")
    require_file(ompl, "ompl_planning.yaml")
    require_file(controllers, "moveit_controllers.yaml")
    require_file(rviz_config, "RViz config")

    robot_description = {
        "robot_description": ParameterValue(
            Command(["xacro ", model]),
            value_type=str
        )
    }

    robot_description_semantic = {
        "robot_description_semantic": read_text(srdf)
    }

    robot_description_kinematics = {
        "robot_description_kinematics": read_yaml(kinematics)
    }

    robot_description_planning = {
        "robot_description_planning": read_yaml(joint_limits)
    }

    ompl_yaml = read_yaml(ompl)
    controllers_yaml = read_yaml(controllers)

    params = [
        robot_description,
        robot_description_semantic,
        robot_description_kinematics,
        robot_description_planning,
        ompl_yaml,
        controllers_yaml,
        {"moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"},
        {"use_sim_time": use_sim_time},
        {"publish_planning_scene": True},
        {"publish_geometry_updates": True},
        {"publish_state_updates": True},
        {"publish_transforms_updates": True},
    ]

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=params,
    )

    rviz = Node(
        condition=IfCondition(use_rviz),
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning,
            {"use_sim_time": use_sim_time},
        ],
    )

    return [move_group, rviz]


def generate_launch_description():
    pkg_moveit = get_package_share_directory("mycobot_moveit_config")
    pkg_desc = get_package_share_directory("mycobot_description")

    default_model = os.path.join(pkg_desc, "urdf", "robots", "mycobot_280.urdf.xacro")
    default_srdf = os.path.join(pkg_moveit, "config", "mycobot_280", "mycobot_280.srdf")
    default_kinematics = os.path.join(pkg_moveit, "config", "mycobot_280", "kinematics.yaml")
    default_joint_limits = os.path.join(pkg_moveit, "config", "mycobot_280", "joint_limits.yaml")
    default_ompl = os.path.join(pkg_moveit, "config", "ompl_planning.yaml")
    default_controllers = os.path.join(pkg_moveit, "config", "mycobot_280", "moveit_controllers.yaml")
    default_rviz = os.path.join(pkg_moveit, "rviz", "move_group.rviz")

    return LaunchDescription([
        DeclareLaunchArgument("model", default_value=default_model),
        DeclareLaunchArgument("srdf", default_value=default_srdf),
        DeclareLaunchArgument("kinematics", default_value=default_kinematics),
        DeclareLaunchArgument("joint_limits", default_value=default_joint_limits),
        DeclareLaunchArgument("ompl", default_value=default_ompl),
        DeclareLaunchArgument("controllers", default_value=default_controllers),
        DeclareLaunchArgument("rviz_config", default_value=default_rviz),
        DeclareLaunchArgument("use_rviz", default_value="true"),
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        OpaqueFunction(function=launch_setup),
    ])