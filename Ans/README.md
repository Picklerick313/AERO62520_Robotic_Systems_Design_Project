# Ans
# Leo Rover – Navigation & Mapping (ROS2 Jazzy)

# Important : This page is under construction

This repository contains the full navigation and mapping pipeline used to enable a Leo Rover to explore an unknown environment, detect colored objects, and navigate to colored bins. It includes:

- Low-level networking between NUC ↔ Raspberry Pi  
- Lidar integration  
- SLAM mapping (Slam Toolbox)  
- Map saving and reuse  
- Localization (AMCL)  
- Navigation (Nav2)  
- Sensor fusion (IMU + odom + lidar)  
- System bring-up and recovery instructions  

This documentation is designed to help:
1. Track code and configuration development.  
2. Recover the system quickly after hardware failure.  
3. Allow anyone to replicate the entire system with minimal expertise.

---

# 1. Clone This Repository

```bash
git clone https://github.com/Picklerick313/AERO62520_Robotic_Systems_Design_Project.git
cd AERO62520_Robotic_Systems_Design_Project/Ans
```

---

# 2. Repository Structure

```
Ans/
├── README.md
├── docs/
│   ├── 00_system_setup_progress.md
│   ├── 01_nuc_configuration.md
│   ├── 02_pi_configuration.md
│   ├── 03_sensor_fusion.md
│   ├── 04_slam_mapping.md
│   ├── 05_localization_nav2.md
├── config/
│   ├── netplan_nuc.yaml
│   ├── netplan_pi.yaml
│   ├── slam_toolbox_params.yaml
│   ├── nav2_params.yaml
│   └── amcl_params.yaml
├── launch/
│   ├── slam_launch.py
│   ├── nav2_bringup_launch.py
├── scripts/
│   └── save_map.sh
├── src/
│   ├── detection/
│   ├── mapping/
│   └── navigation/
├── data/
│   ├── maps/
│   └── rosbags/
└── tests/
    └── verification_checklist.md
```

---

# 3. QUICKSTART (MOST IMPORTANT SECTION)

Follow these exact steps on the **NUC**.

---

## 3.1 Setup ROS2 Environment

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=10" >> ~/.bashrc
echo "export ROS_LOCALHOST_ONLY=0" >> ~/.bashrc
source ~/.bashrc
```

---

## 3.2 Setup Workspace

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
ln -s ~/AERO62520_Robotic_Systems_Design_Project/Ans/src .
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

---

## 3.3 Launch Lidar

```bash
ros2 launch rplidar_ros view_rplidar_a2m12_launch.py
```

Verify in RViz:
- Fixed frame = **laser**
- Topic = **/scan**

---

## 3.4 Run SLAM Toolbox

```bash
ros2 launch Ans/launch/slam_launch.py
```

Open RViz in another window:

```bash
rviz2
```

Set:
- Fixed Frame: **map**
- Add LaserScan → `/scan`
- Add Map

---

## 3.5 Drive Robot to Build Map

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## 3.6 Save Map

```bash
./Ans/scripts/save_map.sh /home/<youruser>/AERO62520_Robotic_Systems_Design_Project/Ans/data/maps/leo_map
```

This creates:

```
leo_map.pgm
leo_map.yaml
```

---

## 3.7 Launch Nav2 with Saved Map

```bash
ros2 launch Ans/launch/nav2_bringup_launch.py map:=/home/<youruser>/AERO62520_Robotic_Systems_Design_Project/Ans/data/maps/leo_map.yaml
```

In RViz:

- Use **2D Pose Estimate** to initialize position  
- Use **2D Nav Goal** to send navigation targets  

---

# 4. Network Setup Summary

### NUC (Static IP: 192.168.12.2)

File: `/etc/netplan/01-nuc-eth.yaml`

```yaml
network:
  version: 2
  renderer: NetworkManager
  ethernets:
    enp114s0:
      addresses:
        - 192.168.12.2/24
      dhcp4: no
```

---

### Raspberry Pi (Static IP: 192.168.12.1)

File: `/etc/netplan/01-pi-eth.yaml` (replace interface name)

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    <PI_INTERFACE>:
      addresses:
        - 192.168.12.1/24
      dhcp4: no
```

---

# 5. Sensor Fusion Requirements

- `/odom` from Pi  
- `/firmware/imu` from Pi  
- `/scan` from NUC Lidar  
- TF tree must contain:  
  `map → odom → base_link → laser`

See docs/03_sensor_fusion.md for instructions.

---

# 6. Object Detection Module

Pipeline:
1. Camera frame → detect color blob  
2. Convert pixel to point in camera frame  
3. Use TF to convert camera → map  
4. Publish Pose → Nav2 Goal  

See docs/06_object_detection.md for reference implementation.

---

# 7. Recovery Steps

If hardware fails:
```bash
git clone https://github.com/Picklerick313/AERO62520_Robotic_Systems_Design_Project.git
cd Ans
```

Rebuild workspace:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Reapply netplan files if needed.

---

# 8. Progress Log (Fill Continuously)

See docs/00_system_setup_progress.md  
Add dates + screenshots + commands run.

---

# 9. Verification Checklist

See tests/verification_checklist.md

---


