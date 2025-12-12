# AERO62520_Robotic_Systems_Design_Project
---
SLAM navigation with Pick and Place on Leo-rover and Mycobot280pi.


![ROS 2 Jazzy](http://googleusercontent.com/image_collection/image_retrieval/11542786739967973228_0)

This repository contains the source code for our group robotics project, featuring an autonomous mobile manipulator capable of SLAM, navigation, and vision-guided pick & place operations. The system is built on **ROS 2 Jazzy Jalisco**.

<p align="center">
  <img src="http://googleusercontent.com/image_collection/image_retrieval/12479818295504692046_0" alt="Robot Prototype" width="600"/>
  <br>
  <em>Figure 1: Conceptual view of the Mobile Manipulator (Replace with your actual robot photo)</em>
</p>

## 🚀 Key Features

| Feature | Description | Visual |
| :--- | :--- | :--- |
| **SLAM & Nav** | Real-time mapping using **Google Cartographer** and **Nav2** for path planning. | <img src="http://googleusercontent.com/image_collection/image_retrieval/11518902879662360098_0" width="200" alt="SLAM Demo" /> |
| **Manipulation** | Trajectory planning with **MoveIt 2** and Graspnet/LLM integration. | <img src="http://googleusercontent.com/image_collection/image_retrieval/11744164540385609507_0" width="200" alt="MoveIt Demo" /> |
| **Mechanical** | Custom-designed primary payload sled and peripheral bins. | *(Add CAD Render)* |

## 🛠️ Prerequisites

* **OS:** Ubuntu 24.04 LTS (Noble Numbat)
* **ROS Distribution:** ROS 2 Jazzy
* **Hardware:**
    * Mobile Base (e.g., Turtlebot/Create3)
    * Manipulator Arm
    * RGB-D Camera (e.g., RealSense/Oak-D)
