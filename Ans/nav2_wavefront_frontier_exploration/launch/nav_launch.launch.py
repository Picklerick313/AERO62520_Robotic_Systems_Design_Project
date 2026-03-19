import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Paths to YOUR package and files
    pkg_dir = get_package_share_directory('nav2_wavefront_frontier_exploration')
    
    # Configuration for sim time (SET TO FALSE FOR REAL ROVER)
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    # Path to the params we just updated
    nav_params = os.path.join(pkg_dir, 'config', 'nav2_params.yaml')
    # Path to the SLAM config
    slam_params = os.path.join(pkg_dir, 'config', 'slam_toolbox.yaml')

    # 2. SLAM Toolbox: This draws the map
    # We use the SLAM parameters to ensure the real LIDAR range is respected
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')),
        launch_arguments={
            'slam_params_file': slam_params,
            'use_sim_time': use_sim_time
        }.items()
    )

    # 3. Nav2: This handles path planning
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')),
        launch_arguments={
            'params_file': nav_params,
            'use_sim_time': use_sim_time,
            'autostart': 'True',
            'use_composition': 'False', # Keeps nodes separate for easier debugging on NUC
        }.items()
    )

    # 4. Wavefront Frontier Exploration: The "Brain"
    wfd_node = Node(
        package='nav2_wavefront_frontier_exploration',
        executable='wavefront_frontier.py', # Ensure this matches your script filename
        name='wavefront_frontier',
        output='screen',
        parameters=[nav_params, {'use_sim_time': use_sim_time}]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false', # Defaulting to false for physical hardware
            description='Use simulation (Gazebo) clock if true'),
        slam_launch,
        nav2_launch,
        wfd_node
    ])