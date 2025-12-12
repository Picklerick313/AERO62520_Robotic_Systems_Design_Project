# Ans
# Navigation & Mapping for Leo Rover — GitHub Repository

Purpose
-------
This repository is designed to:
1. Track code and configuration development for the Navigation & Mapping project.
2. Provide fast recovery steps so devices can be re-programmed quickly after hardware failure.
3. Allow another developer to replicate the entire system and continue work.

Contents
--------
- `docs/`           — step-by-step documentation, run instructions, and troubleshooting.
- `config/`         — all YAML parameter and netplan files used on devices.
- `launch/`         — reproducible launch files for SLAM and Nav2.
- `src/`            — project code (detection, navigation helper scripts).
- `scripts/`        — convenience scripts (save map, start stacks).
- `data/`           — saved maps, rosbags, logs (committed small reference files only).
- `diagrams/`       — network, wiring, TF tree visuals for replication.
- `.github/`        — CI templates and contribution guides.

Current Progress (honest, date-stamped)
---------------------------------------
Status as of [REPOSITORY COMMIT DATE]:

Completed
- NUC (Intel NUC) configured with static Ethernet IP: `192.168.12.2`.
- ROS2 Jazzy installed and configured on NUC.
- RPLIDAR A2M12 driver installed on NUC and verified. `/scan` topic confirmed in RViz.
- Repository structure (docs, config, launch, scripts) initialised and primary docs created.

In progress / remaining
- Raspberry Pi (LeoOS) Ethernet static IP must be finalised to `192.168.12.1` (headless configuration).
- ROS2 multi-machine communication verification (talker on Pi → listener on NUC).
- IMU and odometry publication verification from Pi (`/firmware/imu`, `/odom`).
- TF tree completion and sensor fusion verification.
- SLAM mapping sessions, AMCL localization tuning, Nav2 parameter tuning.
- Colour-detection → pick/place pipeline integration and gripper control on Pi.

Quick status note:
- If you see `/scan` on the NUC and NUC has `192.168.12.2`, you are one Pi configuration step away from full ROS2 multi-machine operation.

Why this repo layout
--------------------
- Everything required to recreate the system is committed (configs, launch, scripts, docs).
- Recovery steps are explicit and in `docs/recovery.md`.
- Detailed run order and verification checklist are in `docs/navmap_quickstart.md`.

How to use this repository
--------------------------
1. Clone the repo on the NUC:


