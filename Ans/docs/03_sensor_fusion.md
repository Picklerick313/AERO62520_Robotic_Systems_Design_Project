#Note : Under Construction
# Sensor Fusion Setup (IMU + Odom + Lidar)

## Required topics
- `/firmware/imu` (from Pi)
- `/odom` (from Pi)
- `/scan` (from NUC)
- TF frames: map → odom → base_link → laser

---

## 1. Check IMU

```bash
ros2 topic echo /firmware/imu -n1
```

## 2. Check Odom

```bash
ros2 topic echo /odom -n1
```

## 3. Check TF Tree

```bash
ros2 run tf2_tools view_frames.py
```

Open generated `frames.pdf`.

---

## 4. Static transform for Lidar

Example (edit numbers):

```bash
ros2 run tf2_ros static_transform_publisher 0.15 0 0.25 0 0 0 base_link laser
```

