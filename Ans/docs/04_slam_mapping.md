# Note: Under construction

# SLAM Mapping Guide

## 1. Launch Lidar

```bash
ros2 launch rplidar_ros view_rplidar_a2m12_launch.py
```

## 2. Launch SLAM

```bash
ros2 launch Ans/launch/slam_launch.py
```

## 3. Open RViz

```bash
rviz2
```

Set:
- Fixed Frame: map

Drive robot with keyboard teleop:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## 4. Save Map

```bash
./Ans/scripts/save_map.sh /home/<youruser>/AERO.../Ans/data/maps/leo_map
```

