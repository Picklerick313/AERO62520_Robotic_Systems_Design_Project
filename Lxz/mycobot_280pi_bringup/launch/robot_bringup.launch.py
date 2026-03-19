from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    port  = LaunchConfiguration("port")
    baud  = LaunchConfiguration("baud")
    speed = LaunchConfiguration("speed")
    xacro_file = LaunchConfiguration("xacro_file")

    robot_description = Command([
        "xacro ", xacro_file,
        " add_world:=false use_gazebo:=false use_gripper:=true"
    ])

    return LaunchDescription([
        DeclareLaunchArgument("port",  default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument("baud",  default_value="115200"),
        DeclareLaunchArgument("speed", default_value="40"),
        DeclareLaunchArgument(
            "xacro_file",
            default_value=PathJoinSubstitution([
                FindPackageShare("mycobot_description"),
                "urdf", "robots", "mycobot_280.urdf.xacro"
            ])
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}]
        ),
        Node(
            package="joint_state_publisher",
            executable="joint_state_publisher"
        ),
        Node(
            package="mycobot_280pi_bringup",
            executable="pymycobot_driver",
            output="screen",
            parameters=[{"port": port, "baud": baud, "speed": speed}]
        ),
    ])