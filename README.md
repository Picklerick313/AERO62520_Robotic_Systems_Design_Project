# AERO62520_Robotic_Systems_Design_Project
---
SLAM navigation with Pick and Place on Leo-rover and Mycobot280pi.


![ROS 2 Jazzy](https://img.shields.io/badge/ROS_2-Jazzy-22314E?style=for-the-badge&logo=ros&logoColor=white)
![Build Status](https://img.shields.io/badge/build-passing-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)

> **A robust mobile manipulation platform capable of SLAM, autonomous navigation, and vision-guided pick & place.**

<div align="center">
  <img src="https://images.unsplash.com/photo-1485827404703-89b55fcc595e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80" alt="Robot Prototype" width="80%" style="border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);"/>
</div>

---

## 🛠️ Tech Stack & Powered By

We leverage the latest industry-standard robotics frameworks:

| Framework | Usage | Logo |
| :--- | :--- | :---: |
| **ROS 2 Jazzy** | Core Middleware & Communication | <img src="https://upload.wikimedia.org/wikipedia/commons/b/bb/Ros_logo.svg" width="60"/> |
| **Nav2** | Autonomous Navigation & Path Planning | <img src="https://navigation.ros.org/_static/nav2_logo.png" width="60"/> |
| **MoveIt 2** | 6-DOF Arm Trajectory Planning | <img src="https://moveit.picknik.ai/assets/logo/moveit_logo-black.png" width="100"/> |
| **Cartographer** | Real-time 2D SLAM (Mapping) | *Google Cartographer* |

---

## 🚀 Key Features

* **🦾 Manipulation:**
    * Vision-guided grasping using **Graspnet/LLM** (adapted from [airs-cuhk/airship](https://github.com/airs-cuhk/airship)).
    * Eye-in-hand camera calibration.
    * Precise trajectory execution via MoveIt 2.
* **🧠 Autonomy:**
    * Simultaneous Localization and Mapping (SLAM) with Google Cartographer.
    * Dynamic obstacle avoidance and path planning with Nav2.
* **⚙️ Mechanical:**
    * Custom-fabricated primary payload sled.
    * Modular peripheral bins for object sorting.
