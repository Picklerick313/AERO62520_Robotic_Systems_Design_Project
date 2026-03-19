
![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-34A853?logo=ros&logoColor=white)
![MoveIt 2](https://img.shields.io/badge/MoveIt-2-02BEEF?logo=ros&logoColor=white)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Ubuntu 24.04](https://img.shields.io/badge/Ubuntu-24.04-E95420?logo=ubuntu&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# 🤖 myCobot Color-Ordered Pick & Place
> **ROS 2 Jazzy** | **MoveIt Task Constructor (MTC)** | **RealSense D435i**

---

This package provides a complete, perception-driven pick-and-place pipeline. It uses real-time HSV and depth filtering to detect objects, orders them by color priority, and dynamically constructs collision-free robotic trajectories using MoveIt Task Constructor (MTC).

---

## ✨ Key Features

- **Color-Sequenced Picking:** Detects colored blocks and publishes ordered grasp poses (`PoseArray`)
- **3D Vision Integration:** Uses a RealSense D435i with depth filtering to localize objects on a table
- **Dynamic Task Generation:** Runs an MTC pipeline using the highest-priority pose
- **Action-Driven Architecture:** Perception fully defines the 6D pick target; client only triggers execution

---

## 🚀 Quick Start

Launch each in separate terminals (ensure robot bringup + MoveIt are running):

### 1. Camera (Aligned depth is critical)
```bash
ros2 launch realsense2_camera rs_launch.py align_depth.enable:=true pointcloud.enable:=true
````

### 2. Vision Perception Node

```bash
ros2 run mycobot_pick_place color_block_detector.py
```

### 3. MoveIt Task Constructor Server

```bash
ros2 run mycobot_pick_place mtc_pick_place_server.py
```

### 4. Trigger the Client

```bash
ros2 run mycobot_pick_place mtc_pick_place_client.py
```

---

## 🎛️ Tunables (Runtime Adjustable)

### Vision Parameters (`/color_block_detector`)

| Parameter                  | Description        | Example                   |
| -------------------------- | ------------------ | ------------------------- |
| `color_order`              | Priority sequence  | `['yellow','red','blue']` |
| `hsv.<color>`              | HSV bounds         | `[0,120,70,10,255,255]`   |
| `min_area_px`              | Noise filter       | `500`                     |
| `max_depth_m`              | Table cutoff       | `0.8`                     |
| `median_depth_kernel`      | Depth denoise      | `5`                       |
| `bilateral / morph_kernel` | Image cleanup      | `5`                       |
| `roi[x,y,w,h]`             | Crop region        | `[100,100,400,300]`       |
| `debug_topics`             | Enable debug image | `true`                    |

### Example Live Tuning

```bash
ros2 param set /color_block_detector hsv.red "[0,120,70,10,255,255]"
ros2 param set /color_block_detector color_order "['red','green','blue']"
```

---

## ⚙️ MTC Server Parameters

Defined in `mtc_pick_place_server.py`:

| Category   | Parameters                                             |
| ---------- | ------------------------------------------------------ |
| Kinematics | `arm_group`, `eef_group`, `grasp_frame`, `world_frame` |
| Clearances | `approach_distance`, `lift_distance`                   |
| Dynamics   | `vel_scale`, `acc_scale`                               |
| Placement  | `place_pose_6` → `[x,y,z,r,p,y]`                       |

---

## 🔄 Data Flow

1. Vision node publishes ordered `PoseArray` → `/color_blocks/poses`
2. MTC server consumes first pose and builds:

   * approach → grasp → lift → retreat → place
3. Client sends goal containing **only place pose**

---

## 🎙️ Future Expansion: AI Voice Agents

Enable natural interaction like:

> *"Hey Cobot, sort red blocks first."*

### Proposed Local Voice Stack

* **Agent Orchestration:** LiveKit Agents

  * Handles real-time pipeline, interruptions, and turn-taking

* **Speech-to-Text (STT):** faster-whisper (Whisper large-v3-turbo)

  * Accurate, low CPU usage, robust in noisy environments

* **LLM:** Ollama (llama3 8B / gemma)

  * Converts intent → ROS2 commands
  * Example:

    ```bash
    ros2 param set /color_block_detector color_order "['red']"
    ```

* **Text-to-Speech (TTS):** Kokoro TTS / Piper

  * Fast, local, expressive voice responses

---

## 🛠️ Debugging Tips

```bash
# Check detected poses
ros2 topic echo /color_blocks/poses -n1
```

* 📸 View debug image in RViz → Image display → `color_blocks/debug`
* 🚨 No poses? Lower `min_area_px`, adjust HSV, expand ROI
* 🕳️ Depth = 0? Ensure `align_depth.enable:=true`
* 🛑 Planning fails? Lower speed or increase clearances

---

## 🗺️ Roadmap

* [ ] Orientation estimation via contour principal axis
* [ ] Multi-block queue execution (full PoseArray)
* [ ] Voice control node (LiveKit + TTS)
* [ ] Dynamic drop bins (topic-driven placement)
* [ ] Environment collision modeling (table, walls)

```
```
