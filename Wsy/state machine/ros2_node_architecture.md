# ROS2 Node Architecture

This document describes the main ROS2 nodes, actions, and services used in the robot system.


robot_state_machine_node
│
├── mapping_manager_node
│   ├── SLAM toolbox / mapping node
│   ├── map saver service
│   └── start pose storage
│
├── vision_node
│   ├── camera topic subscriber
│   ├── detect_block_once service
│   ├── detect_bin_once service
│   └── set_vision_mode service
│
├── approach_object_node
│   ├── Nav2 NavigateToPose action client
│   ├── local alignment controller
│   └── ApproachTarget action server
│
├── grasp_node
│   ├── arm controller
│   ├── gripper service
│   └── GraspBlock action server
│
├── place_node
│   ├── bin vision
│   ├── arm controller
│   ├── gripper service
│   └── PlaceBlock action server
│
└── operator_interface_node
    └── recovery command service / topic
