from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """
    阶段 A：只找白色 bin，用于导航。

    - 2D 检测：只启用 white 的 HSV（tools/color_ranges_white_only.yaml）
    - 3D 投影：使用深度 + 尺度过滤，将 blob:white 分类为 bin:white / block:white / background
    - 导航侧：只订阅 /color_blobs_3d，并筛选 class_id == \"bin:white\" 作为目标。
    """

    detector = Node(
        package="color_blob_vision",
        executable="color_blob_detector",
        name="color_blob_detector_white",
        parameters=[
            {
                "yaml_path": "/home/student24/robotproject/tools/color_ranges_white_only.yaml",
                "image_topic": "/camera/camera/color/image_raw",
                "output_topic": "/color_blobs",
                # 白 bin 通常占据较大面积；提高 min_area 以过滤小白块/反光误检
                "min_area": 12000,
                # 增大形态学核，帮助把碎白区域连接成一个整体轮廓
                "kernel_size": 9,
            }
        ],
    )

    depth_to_3d = Node(
        package="color_blob_vision",
        executable="blob_depth_to_3d",
        name="blob_depth_to_3d_white",
        parameters=[
            {
                "camera_info_topic": "/camera/camera/color/camera_info",
                "depth_topic": "/camera/camera/aligned_depth_to_color/image_raw",
                "blobs_2d_topic": "/color_blobs",
                "output_topic": "/color_blobs_3d",
                # 白 bin 用于导航，可以稍微看远一些（例如 1.0m 内）
                "depth_min_m": 0.05,
                "depth_max_m": 1.00,
                "block_size_max_m": 0.10,
                "bin_size_min_m": 0.15,
                "bin_size_max_m": 0.35,
            }
        ],
    )

    return LaunchDescription(
        [
            detector,
            depth_to_3d,
            # 你的导航/行为节点可以在自己的包里另写 launch，
            # 或者在这里一起起，只要订阅 /color_blobs_3d，筛选 bin:white 即可。
        ]
    )


