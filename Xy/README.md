# Xy `src` Contribution Overview

This README describes the work contributed in `Xy/ros_nd2/src`, rather than the whole repository.

The focus of this part is the ROS 2 perception pipeline that supports:

* white bin detection for navigation/search
* colored block and bin detection for manipulation
* 3D localization from aligned depth
* handoff from perception to navigation and manipulator logic

---

## What Was Implemented

The `src` workspace is centered on the `color_blob_vision` package and the launch/documentation files around it.

The contribution includes:

* HSV-based 2D color blob detection from RGB images
* depth-based 3D projection for object position estimation
* block/bin classification using projected size cues
* temporal smoothing and confirmation to improve output stability
* debug tools for terminal output, RViz markers, and annotated images
* launch flows for both white-bin search and colored pick-and-place
* manager nodes to support integrated runtime coordination
* handoff notes explaining how this perception pipeline connects to navigation and manipulation

---

## Source Structure

```bash
Xy/ros_nd2/src/color_blob_vision/
├── color_blob_vision/
│   ├── color_blob_detector.py
│   ├── blob_depth_to_3d.py
│   ├── blob_depth_to_3d_smoothed.py
│   ├── perception_manager.py
│   ├── task_manager.py
│   ├── color_blob_run_recorder.py
│   ├── color_blob_summary.py
│   ├── color_blob_markers.py
│   └── color_blob_debug_image.py
├── launch/
│   ├── find_white_bin.launch.py
│   ├── pick_and_place_blocks.launch.py
│   └── vision_pipeline_manager.launch.py
├── test/
├── manipulator_handoff.md
├── navigation_handoff.md
├── offline_vs_real_pipeline.md
├── package.xml
├── setup.cfg
└── setup.py
```

---

## Main Functional Parts

### 1. 2D Detection

`color_blob_detector.py` performs HSV-based segmentation and contour filtering, then publishes 2D detections as `vision_msgs/Detection2DArray`.

Each detection contains:

* a color label
* center position in the image
* bounding box size
* orientation estimated from the rotated rectangle

### 2. 3D Localization

`blob_depth_to_3d.py` and `blob_depth_to_3d_smoothed.py` combine:

* 2D detections
* aligned depth images
* camera intrinsics

to estimate:

* 3D object position in the camera frame
* yaw/orientation information
* coarse object type such as `block:<color>` or `bin:<color>`

The smoothed variant also adds confirmation and temporal filtering to make detections more stable across frames.

### 3. Runtime Coordination

The newer files in this `src` contribution expand the pipeline beyond isolated nodes:

* `perception_manager.py` coordinates perception-related runtime behavior
* `task_manager.py` supports higher-level task flow
* `vision_pipeline_manager.launch.py` provides an integrated launch entry point
* `color_blob_run_recorder.py` helps record or summarize runs for debugging and evaluation

### 4. Debugging and Integration Support

To make the perception stack easier to inspect and connect with the rest of the robot system, this work also includes:

* `color_blob_summary.py` for terminal summaries
* `color_blob_markers.py` for RViz visualization
* `color_blob_debug_image.py` for annotated image output
* `navigation_handoff.md` for navigation-side integration notes
* `manipulator_handoff.md` for manipulator-side integration notes
* `offline_vs_real_pipeline.md` for explaining differences between offline and real deployment flows

---

## Operating Modes

This `src` work supports two main modes:

### Stage A: White bin detection

Used in navigation or search mode, where the system focuses on finding white bins and publishing the corresponding detections for downstream logic.

### Stage B: Colored object detection

Used in manipulation mode, where the pipeline detects `red`, `blue`, `yellow`, and `white` targets and classifies them as blocks or bins for pick-and-place tasks.

---

## Repository Hygiene

This area should mainly keep source and documentation.

Generated workspace artifacts such as `build/`, `install/`, `log/`, `__pycache__/`, and `*.pyc` should not be committed.

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
