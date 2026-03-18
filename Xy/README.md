# color_blob_vision

A ROS 2 vision package for **color blob detection, 3D localization, and object classification** in robot manipulation tasks.
This project is designed for workflows such as **finding white bins, detecting colored blocks, estimating 3D positions from depth images, and supporting pick-and-place tasks**.

The system is organized into two main stages:

* **Stage A: White bin detection**

  * Used in navigation or search mode, where only white bins are detected.
* **Stage B: Colored block / bin detection**

  * Used in manipulation mode, where red, blue, yellow, and white objects are detected and classified as either blocks or bins.

---

## Features

### 1. 2D Color Blob Detection

The package uses HSV-based image segmentation to detect colored blobs from RGB images and publishes the results as `vision_msgs/Detection2DArray`.

Each 2D detection includes:

* color label (for example, `blob:red`)
* 2D center position
* bounding box size
* in-plane orientation angle estimated from the minimum-area rectangle

### 2. 3D Projection from Depth

The package combines 2D detections, aligned depth images, and camera intrinsics to estimate:

* 3D position `(x, y, z)` in the camera frame
* yaw angle for object orientation

It also uses estimated object size in 3D to classify detections as:

* `block:<color>`
* `bin:<color>`

### 3. Multi-frame Smoothing and Confirmation

The 3D node includes lightweight tracking and exponential moving average smoothing to:

* reduce false positives
* confirm detections across multiple frames
* stabilize 3D position and orientation estimates
* improve block/bin classification consistency

### 4. Debugging and Visualization Tools

The package also provides several helper nodes:

* **color_blob_summary**: prints detected object information in the terminal
* **color_blob_markers**: publishes RViz markers for visualization
* **color_blob_debug_image**: overlays bounding boxes, labels, centers, and angles on the image

---

## Project Structure

```bash
color_blob_vision/
├── launch/
│   ├── find_white_bin.launch.py
│   └── pick_and_place_blocks.launch.py
├── color_blob_vision/
│   ├── color_blob_detector.py
│   ├── blob_depth_to_3d_smoothed.py
│   ├── color_blob_summary.py
│   ├── color_blob_markers.py
│   └── color_blob_debug_image.py
├── package.xml
├── setup.py
└── README.md
```

---

## Nodes

### `color_blob_detector`

A 2D color blob detection node.

**Input:**

* RGB image topic (default example: `/camera/camera/color/image_raw`)

**Output:**

* `/color_blobs` (`vision_msgs/Detection2DArray`)

**Main functionality:**

* loads HSV thresholds from a YAML file
* supports multiple HSV ranges for a single color
* applies minimum area filtering and morphological operations
* estimates object orientation and stores it in `bbox.center.theta`

---

### `blob_depth_to_3d`

A 3D projection node.
In this project, the default executable points to the smoothed version.

**Input:**

* aligned depth image
* camera intrinsic parameters
* `/color_blobs`

**Output:**

* `/color_blobs_3d` (`vision_msgs/Detection3DArray`)

**Main functionality:**

* estimates depth using the median value of a depth patch
* computes 3D position from image coordinates and depth
* estimates physical object size
* classifies objects as blocks or bins
* applies lightweight tracking, confirmation, and EMA smoothing

---

### `color_blob_summary`

A terminal debugging node.

**Input:**

* `/color_blobs_3d`

**Output:**

* console logs showing object color, 3D position, yaw, and score

---

### `color_blob_markers`

An RViz visualization node.

**Input:**

* `/color_blobs_3d`

**Output:**

* `/color_blobs_markers` (`visualization_msgs/MarkerArray`)

---

### `color_blob_debug_image`

An image debugging node.

**Input:**

* raw color image
* `/color_blobs`

**Output:**

* `/color_blobs/debug_image`

**Functionality:**

* draws bounding boxes, labels, confidence scores, and centers
* re-runs contour extraction inside the ROI
* visualizes rotated rectangles and principal axes for angle debugging

---

## Launch Files

### `find_white_bin.launch.py`

Used for **Stage A: white bin detection**, typically during navigation or search.

This launch file:

* enables only the white HSV configuration
* runs 2D detection and 3D projection
* outputs white bin detections for downstream navigation logic

---

### `pick_and_place_blocks.launch.py`

Used for **Stage B: colored block and bin detection**, typically during manipulation.

This launch file:

* detects `red`, `blue`, `yellow`, and `white`
* classifies objects as either `block:<color>` or `bin:<color>`
* can optionally launch:

  * `color_blob_markers`
  * `color_blob_summary`

---

## Dependencies

This package is a ROS 2 Python package and depends on:

* `rclpy`
* `sensor_msgs`
* `vision_msgs`
* `visualization_msgs`
* `cv_bridge`
* `message_filters`
* `OpenCV (cv2)`
* `numpy`
* `PyYAML`

The default topics in the current codebase are compatible with a RealSense-style setup, for example:

* `/camera/camera/color/image_raw`
* `/camera/camera/color/camera_info`
* `/camera/camera/aligned_depth_to_color/image_raw`

---

## Build and Installation

Place the package inside the `src/` directory of your ROS 2 workspace, then build it with:

```bash
cd ~/your_ros2_ws
colcon build --packages-select color_blob_vision
source install/setup.bash
```

---

## Usage

### A. Detect only white bins

```bash
ros2 launch color_blob_vision find_white_bin.launch.py
```

This mode is intended for navigation or search tasks.

Relevant output topics:

* `/color_blobs`
* `/color_blobs_3d`

A downstream navigation module can subscribe to `/color_blobs_3d` and filter detections by:

```text
class_id == "bin:white"
```

---

### B. Detect colored blocks and bins

```bash
ros2 launch color_blob_vision pick_and_place_blocks.launch.py
```

This mode is intended for pick-and-place tasks.

To enable RViz markers as well:

```bash
ros2 launch color_blob_vision pick_and_place_blocks.launch.py use_markers:=true
```

---

## Important Parameters

### `color_blob_detector`

* `yaml_path`: path to the HSV configuration file
* `image_topic`: input image topic
* `output_topic`: output topic for 2D detections
* `min_area`: minimum contour area
* `kernel_size`: morphology kernel size
* `resize_factor`: image downscaling factor

### `blob_depth_to_3d`

* `depth_topic`
* `camera_info_topic`
* `blobs_2d_topic`
* `output_topic`
* `patch_radius`
* `depth_min_m`
* `depth_max_m`
* `block_size_max_m`
* `bin_size_min_m`
* `bin_size_max_m`

Tracking and smoothing parameters include:

* `block_match_dist_m`
* `bin_match_dist_m`
* `confirm_hits_block`
* `confirm_hits_bin`
* `max_misses_block`
* `max_misses_bin`
* `pos_alpha_block`
* `pos_alpha_bin`
* `yaw_alpha_block`
* `yaw_alpha_bin`

---

## Output Format

### 2D Detection Output

Each detection in `/color_blobs` contains information such as:

* `class_id = "blob:red"`
* `bbox.center.position = (u, v)`
* `bbox.size_x, bbox.size_y`
* `bbox.center.theta = grasp orientation angle in radians`

### 3D Detection Output

Each detection in `/color_blobs_3d` contains information such as:

* `class_id = "block:red"` or `"bin:white"`
* `pose.position = (x, y, z)` in meters
* `pose.orientation = quaternion converted from yaw`

---

## Application Scenarios

This package can be used for:

* robot visual navigation
* color-based object detection
* block and bin classification
* robotic pick-and-place tasks
* lightweight RGB-D perception experiments

---

## Possible Future Improvements

* support more color categories
* improve robustness under changing lighting conditions
* add stronger temporal filtering such as a Kalman filter
* integrate TF transforms to publish detections in the robot base frame
* connect the output to a grasp planner or task-level controller
* make YAML configuration and topic management more modular

---

## Notes

In the current version, some launch files use absolute local file paths for YAML configuration files.
For better portability, these configuration files should ideally be moved into the package and loaded using package share paths.

---

## Author

Maintainer: `Kyra`
