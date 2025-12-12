# Ans
cat > README.md <<'EOF'
# Leo Rover — Navigation & Mapping (ROS2 Jazzy)

Repository: https://github.com/Picklerick313/AERO62520_Robotic_Systems_Design_Project (Ans folder)

Purpose
-------
This repository provides all configuration, launch files, scripts and documentation needed to:
1. Track code and configuration development for navigation and mapping.
2. Restore devices rapidly after hardware failure (reflash & reconfigure).
3. Allow others to replicate the full mapping and navigation pipeline.

Folder overview (inside Ans/)
- docs/: documentation and run/recovery instructions
- config/: netplan and ROS parameter files
- launch/: SLAM and Nav2 launches
- scripts/: utilities (save map)
- src/: robot packages (detection, mapping, navigation)
- data/: saved maps and rosbags for reproducibility
- tests/: verification checklists

Progress (honest)
-----------------
Completed:
- NUC static IP configured: 192.168.12.2 (config/netplan_nuc.yaml)
- ROS2 Jazzy installed on NUC; RPLidar driver installed and /scan validated in RViz
- Basic repo structure and initial documentation created

Remaining:
- Configure Raspberry Pi netplan -> set static IP 192.168.12.1
- Ensure Pi publishes /odom and /firmware/imu
- Verify ROS2 multi-machine communication (Pi <-> NUC)
- Build TF tree and perform sensor fusion (IMU+odom+lidar)
- Run SLAM, save map, launch AMCL, tune Nav2
- Implement colour detection -> pick/place integration

How to clone (on NUC)
---------------------
git clone https://github.com/Picklerick313/AERO62520_Robotic_Systems_Design_Project.git
cd AERO62520_Robotic_Systems_Design_Project/Ans

Quick start (NUC)
-----------------
1. Source ROS2:
   source /opt/ros/jazzy/setup.bash
2. Create or use ROS workspace and link Ans/src into it:
   mkdir -p ~/ros2_ws/src
   cd ~/ros2_ws/src
   ln -s ~/AERO62520_Robotic_Systems_Design_Project/Ans/src .
   cd ~/ros2_ws
   colcon build --symlink-install
   source install/setup.bash
3. Launch Lidar and SLAM, drive for mapping, save map (see docs/navmap_quickstart.md)

Recovery & replication
----------------------
Full step-by-step recovery instructions and exact commands are in docs/recovery.md.

Contact
-------
Maintainer: Picklerick313 (GitHub)
EOF



