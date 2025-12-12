from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
import os

def generate_launch_description():
    params_file = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'nav2_params.yaml'
    )

    map_arg = DeclareLaunchArgument(
        'map',
        default_value='',
        description='Full path to map yaml'
    )

    return LaunchDescription([
        map_arg,
        Node(
            package='nav2_bringup',
            executable='bringup_launch.py',
            output='screen',
            parameters=[params_file]
        )
    ])

