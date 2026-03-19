import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_leo_wfd_sim = get_package_share_directory('leo_wfd_simulation')
    pkg_leo_gz_bringup = get_package_share_directory('leo_gz_bringup')
    world_file = os.path.join(pkg_leo_wfd_sim, 'worlds', 'room_maze.sdf')

    # 1. Start the Leo Rover Simulation
    leo_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_leo_gz_bringup, 'launch', 'leo_gz.launch.py')
        ),
        launch_arguments={'sim_world': world_file}.items()
    )

    # 2. Add the ROS-Gazebo Bridge ONLY for LiDAR
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        output='screen'
    )

    return LaunchDescription([
        leo_bringup,
        gz_bridge
    ])