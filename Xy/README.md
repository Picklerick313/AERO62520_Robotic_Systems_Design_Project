# Xy Contribution Overview

This README documents the work completed in `Xy/ros_nd2/src`, with a focus on the perception and pipeline integration components developed for the project.

The main goal of this contribution was not just to make a detector run, but to build a perception module that could actually support the robot's full task flow: from finding white bins during navigation, to identifying colored objects during manipulation, to providing structured outputs that other subsystems could directly consume.

In practical terms, this work aimed to achieve three things:

* build a usable RGB-D perception pipeline in ROS 2
* improve reliability beyond one-frame image detection by adding 3D reasoning and temporal stability
* make the perception system easier to hand off, integrate, debug, and extend within the larger robot project

---

## Contribution Goals

This part of the project was designed to solve several real integration problems:

* how to detect task-relevant objects from camera images in a lightweight and explainable way
* how to convert 2D image detections into 3D positions meaningful for robot action
* how to distinguish blocks from bins instead of only reporting raw colored blobs
* how to reduce unstable detections so the output is more useful to downstream modules
* how to connect perception outputs to navigation and manipulator workflows rather than leaving them as isolated demo nodes

So the work in `src` was developed not only as computer vision code, but as a bridge between sensing and robot behavior.

---

## What Was Achieved

The final contribution includes a complete ROS 2 perception package and supporting integration files that together provide:

* 2D HSV-based color blob detection for white, red, blue, and yellow targets
* 3D position estimation from aligned depth and camera intrinsics
* object-type classification into `block:<color>` and `bin:<color>`
* smoothed and confirmed multi-frame outputs for more stable perception
* launch flows for both navigation-oriented and manipulation-oriented modes
* debugging tools for visual verification, terminal summaries, and RViz inspection
* manager nodes to support pipeline coordination at a higher level
* handoff documentation to help connect this work to navigation and manipulator subsystems

This means the contribution moved the system from “camera sees colored areas” to “robot receives structured, task-relevant object information.”

---

## Why This Work Matters

A major part of the effort here was improving the perception stack from a basic detector into something more useful for a real robot pipeline.

Key improvements include:

### 1. From 2D vision to action-relevant 3D perception

Instead of stopping at image-plane detections, the pipeline projects detections into 3D space using depth data. This makes the output much more useful for downstream decision-making, because robot modules typically need object positions in space, not just pixel coordinates.

### 2. From raw color blobs to semantic task objects

The system does not only say “this is red” or “this is white.” It also estimates object scale from depth and uses that information to classify detections into task-relevant categories such as blocks and bins. That makes the output directly aligned with task logic.

### 3. From unstable frame-wise detections to more robust outputs

A common issue in lightweight vision pipelines is detection flicker. This contribution addressed that by adding confirmation logic, lightweight tracking, and temporal smoothing so that detections are more consistent across time.

### 4. From isolated nodes to an integratable subsystem

Beyond the core detector nodes, the work also includes runtime coordination files, launch integration, debugging tools, and handoff notes. That makes it easier for the perception module to be used by teammates rather than remaining a standalone experiment.

---

## Scope of Work

The implementation in `Xy/ros_nd2/src/color_blob_vision` covers the following areas.

### Core perception

* HSV-based blob detection from RGB images
* contour filtering and rotated bounding box estimation
* 2D detection publishing through ROS 2 messages
* depth-based 3D projection using aligned RGB-D data
* size-aware classification into blocks and bins

### Robustness improvements

* temporal smoothing for position and yaw
* multi-frame confirmation logic
* lightweight detection association across frames
* more stable outputs for downstream consumers

### System integration

* separate launch flows for search mode and manipulation mode
* pipeline coordination through manager-style nodes
* documentation for navigation-side and manipulator-side handoff
* notes comparing offline experiments and real deployment behavior

### Debugging and evaluation support

* annotated debug image outputs
* terminal detection summaries
* RViz marker visualization
* run recording support for experiments and verification

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

## Main Components and My Work

### `color_blob_detector.py`

This node performs HSV-based segmentation and contour analysis to detect colored regions in RGB images.

My work here focused on:

* building a lightweight but practical color-based detector
* supporting multiple task colors
* producing structured 2D detections rather than ad hoc image overlays
* extracting orientation information from rotated rectangles for downstream use

This formed the foundation of the perception pipeline.

### `blob_depth_to_3d.py` and `blob_depth_to_3d_smoothed.py`

These nodes extend 2D detections into 3D by combining image detections, aligned depth, and camera intrinsics.

My work here focused on:

* converting image-plane detections into meaningful 3D positions
* estimating object size in metric space
* classifying objects as blocks or bins
* reducing output instability through smoothing and confirmation logic

This was one of the most important steps in making the perception output useful for robot behavior.

### `perception_manager.py` and `task_manager.py`

These files expand the system from individual nodes into something closer to a coordinated runtime pipeline.

My work here focused on:

* supporting higher-level orchestration
* improving how perception components are organized during execution
* moving the package toward a more integrated system rather than disconnected scripts

### `vision_pipeline_manager.launch.py`

This launch file helps unify the perception pipeline into a more manageable entry point.

Its role is important because it reflects a shift from testing individual pieces to managing the full workflow in a cleaner way.

### Debugging and support tools

The following files were added or maintained to support development, verification, and team integration:

* `color_blob_summary.py`
* `color_blob_markers.py`
* `color_blob_debug_image.py`
* `color_blob_run_recorder.py`

These tools matter because they make the system easier to validate, explain, and troubleshoot during experiments and demos.

### Handoff and integration documents

The following documents were written to help the rest of the team understand how to use or integrate this perception work:

* `navigation_handoff.md`
* `manipulator_handoff.md`
* `offline_vs_real_pipeline.md`

This documentation is part of the contribution itself, because successful robotics work depends not only on code working locally, but on other subsystems being able to connect to it.

---

## Operating Modes

This contribution supports two main task stages.

### Stage A: White bin detection for navigation/search

In this mode, the system focuses on detecting white bins and estimating their 3D positions. The goal is to support navigation or search-related logic by providing clear bin detections to downstream modules.

### Stage B: Colored object detection for manipulation

In this mode, the system detects colored objects and classifies them as blocks or bins. The goal is to support manipulation tasks such as pick-and-place with more task-relevant semantic output.

This dual-mode structure reflects the broader project requirement that perception must serve different robot behaviors at different times.

---

## Key Outcomes

The most important outcomes of this work are:

* a working ROS 2 perception package tailored to the project task
* a transition from simple 2D color detection to 3D task-aware perception
* improved stability and usability through smoothing and confirmation
* perception outputs that are more directly useful for navigation and manipulation
* better integration readiness through launch files, manager nodes, and handoff documentation

In other words, this contribution did not just implement detection algorithms. It established a more complete perception subsystem that supports the robot's operational pipeline.

---

## Build and Installation

Place the package inside the `src/` directory of your ROS 2 workspace, then build it with:

```bash
cd ~/your_ros2_ws
colcon build --packages-select color_blob_vision
source install/setup.bash
```

---

## Example Usage

### White-bin detection mode

```bash
ros2 launch color_blob_vision find_white_bin.launch.py
```

This mode is intended for navigation or search tasks.

### Colored block/bin mode

```bash
ros2 launch color_blob_vision pick_and_place_blocks.launch.py
```

To enable RViz markers:

```bash
ros2 launch color_blob_vision pick_and_place_blocks.launch.py use_markers:=true
```

---

## Reflection and Future Improvements

There are still several directions that could make the system stronger:

* improving robustness under changing lighting conditions
* adding more modular configuration management
* replacing lightweight smoothing with more advanced filtering if needed
* publishing detections in additional coordinate frames through TF integration
* connecting outputs more tightly with grasp planning or task-level controllers

Even so, the current contribution already provides a solid and usable base for perception-driven robot tasks in this project.

---

## Author

Maintainer: `Kyra`

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
