from launch import LaunchDescription
from launch_ros.actions import Node
import os

def generate_launch_description():
    config = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'slam_toolbox_params.yaml'
    )

    return LaunchDescription([
        Node(
            package='slam_toolbox',
            executable='online_async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[config]
        )
    ])
