#Note : Under Construction

# Localization & Nav2 Guide

## 1. Launch Nav2

```bash
ros2 launch Ans/launch/nav2_bringup_launch.py map:=/path/to/map.yaml
```

---

## 2. In RViz

- Set initial pose using **2D Pose Estimate**  
- Send goal using **2D Nav Goal**

---

## 3. Check velocity command output

```bash
ros2 topic echo /cmd_vel -n1
```

Pi must subscribe to `/cmd_vel`.

