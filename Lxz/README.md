## To-dos:
- [x] Test code for pick and place
- [ ] Plan trajectory with Moveit2 
- [ ] Eye-in-hand calibration
- [ ] Implement Graspnet/LLM based on [This open project](https://github.com/airs-cuhk/airship/tree/main) 

---
The API (mycobotpy) can manipulate the robot just fine,However, Moveit2 is chosen for later vision-guided pick and place
---
# MoveIt2 Configuration for myCobot 280Pi

Comprehensive documentation for setting up and running MoveIt2 with the myCobot 280Pi robotic arm on ROS2 Jazzy.

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Usage](#usage)
- [Code Design](#code-design)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Roadmap](#roadmap)

---

## Overview

This project provides a complete MoveIt2 configuration for the myCobot 280Pi robotic arm, enabling motion planning, manipulation, and control through ROS2 Jazzy. 

### Features
- ✅ Full MoveIt2 integration
- ✅ URDF robot description
- ✅ Motion planning with multiple planners
- ✅ Collision detection
- ✅ Simulation support (RViz2)
- ✅ Real hardware interface

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ROS2 Jazzy Layer                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌─────────────────────────┐    │
│  │   MoveIt2    │◄────►│  Planning Pipelines     │    │
│  │   Framework  │      │  - OMPL                 │    │
│  └──────┬───────┘      │  - Pilz Industrial      │    │
│         │              │  - CHOMP                │    │
│         │              └─────────────────────────┘    │
│         ▼                                             │
│  ┌──────────────────────────────────────────┐        │
│  │     Robot Description (URDF/XACRO)       │        │
│  │  - mycobot_description package           │        │
│  └──────────────┬───────────────────────────┘        │
│                 │                                      │
│                 ▼                                      │
│  ┌──────────────────────────────────────────┐        │
│  │        Hardware Interface Layer          │        │
│  │  - ros2_control                          │        │
│  │  - Joint State Publisher                │        │
│  └──────────────┬───────────────────────────┘        │
│                 │                                      │
└─────────────────┼──────────────────────────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  myCobot 280Pi  │
         │   Hardware      │
         └─────────────────┘
```

---

## Prerequisites

### Hardware Requirements
- myCobot 280Pi robotic arm
- Ubuntu 24.04


### Software Requirements
- **ROS2 Jazzy Jalisco**
- **MoveIt2** (Jazzy version)
- **Python 3.10+**
- **colcon** build tool

---

## Installation

### Step 1: Install ROS2 Jazzy

```bash
# Set up ROS2 repositories
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# Add ROS2 apt repository
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros. key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(.  /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list. d/ros2.list > /dev/null

# Install ROS2 Jazzy
sudo apt update
sudo apt install ros-jazzy-desktop
```

### Step 2: Install MoveIt2

```bash
sudo apt install ros-jazzy-moveit
```

### Step 3: Install Additional Dependencies

```bash
sudo apt install -y \
    ros-jazzy-moveit-setup-assistant \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    python3-colcon-common-extensions \
    python3-rosdep
```

### Step 4: Create Workspace

```bash
# Create workspace
mkdir -p ~/grasp_workspace/src
cd ~/grasp_workspace

# Initialize rosdep (if not already done)
sudo rosdep init
rosdep update
```

### Step 5: Clone myCobot Description Package

```bash
cd ~/grasp_workspace/src

# Clone the myCobot ROS2 repository
git clone https://github.com/elephantrobotics/mycobot_ros2.git -b jazzy

# If jazzy branch doesn't exist, try humble or main and adapt
# git clone https://github.com/elephantrobotics/mycobot_ros2.git
```

### Step 6: Install Dependencies and Build

```bash
cd ~/grasp_workspace

# Install dependencies
rosdep install --from-paths src --ignore-src -r -y

# Build the workspace
colcon build --symlink-install

# Source the workspace
source install/setup.bash
```

### Step 7: Add to . bashrc (Optional but Recommended)

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "source ~/grasp_workspace/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## Project Structure

```
grasp_workspace/
├── src/
│   ├── mycobot_ros2/                    # Robot description package
│   │   ├── mycobot_description/
│   │   │   ├── urdf/
│   │   │   │   ├── mycobot_280pi.urdf.xacro
│   │   │   │   └── mycobot_280pi.urdf
│   │   │   ├── meshes/                  # 3D mesh files
│   │   │   ├── config/                  # Configuration files
│   │   │   └── launch/                  # Launch files
│   │   └── mycobot_moveit_config/       # MoveIt configuration
│   │       ├── config/
│   │       │   ├── moveit. yaml
│   │       │   ├── kinematics.yaml
│   │       │   ├── joint_limits.yaml
│   │       │   ├── pilz_cartesian_limits.yaml
│   │       │   └── sensors_3d.yaml
│   │       ├── launch/
│   │       │   ├── demo. launch. py       # Main demo launcher
│   │       │   ├── move_group.launch.py
│   │       │   └── warehouse_db.launch.py
│   │       └── srdf/
│   │           └── mycobot_280pi.srdf   # Semantic robot description
│   └── [your_custom_packages]/
├── build/
├── install/
└── log/
```

---

## Configuration

### MoveIt Setup Assistant

To configure or reconfigure MoveIt2 for your robot:

```bash
# Ensure workspace is sourced
source ~/grasp_workspace/install/setup.bash

# Launch MoveIt Setup Assistant
ros2 run moveit_setup_assistant moveit_setup_assistant
```

#### Configuration Steps: 

1. **Start Screen**
   - Load URDF from:  `~/grasp_workspace/src/mycobot_ros2/mycobot_description/urdf/mycobot_280pi.urdf`
   - Click "Load Files"

2. **Self-Collisions**
   - Generate collision matrix
   - Adjust sampling density (default: 10000)

3. **Virtual Joints**
   - Add fixed joint to world frame
   - Name: `virtual_joint`
   - Type: `fixed`

4. **Planning Groups**
   - Create group:  `arm`
   - Add joints: `joint1` through `joint6`
   - Kinematic solver: `kdl_kinematics_plugin/KDLKinematicsPlugin`

5. **Robot Poses**
   - Add named poses (e.g., "home", "ready", "sleep")

6. **End Effectors**
   - Define gripper as end effector
   - Parent group: `arm`

7. **ROS2 Controllers**
   - Configure `joint_trajectory_controller`

8. **Author Information**
   - Fill in your details

9. **Generate Files**
   - Output path: `~/grasp_workspace/src/mycobot_moveit_config`

---

## Usage

### 1. Verify Package Installation

```bash
# Check if package is found
ros2 pkg list | grep mycobot

# Expected output:
# mycobot_description
# mycobot_moveit_config
```

### 2. Launch Simulation (RViz2)

```bash
# Terminal 1: Launch MoveIt demo
ros2 launch mycobot_moveit_config demo.launch.py
```

This will open RViz2 with: 
- Robot model visualization
- Interactive motion planning
- Planning scene visualization

### 3. Using MoveIt with Python

Create a Python script to control the robot: 

```python
#!/usr/bin/env python3

import rclpy
from rclpy. node import Node
from moveit_msgs.msg import MoveGroupActionGoal
from geometry_msgs.msg import Pose, PoseStamped
from moveit. planning import MoveGroupInterface

class MyCobotController(Node):
    def __init__(self):
        super().__init__('mycobot_controller')
        
        # Initialize MoveIt interface
        self.move_group = MoveGroupInterface(
            node=self,
            group_name="arm",
            robot_description="robot_description"
        )
        
        self.get_logger().info("MoveIt interface initialized")
    
    def move_to_pose(self, x, y, z, roll, pitch, yaw):
        """Move robot to target pose"""
        
        # Set target pose
        target_pose = Pose()
        target_pose.position. x = x
        target_pose.position.y = y
        target_pose.position.z = z
        
        # Convert RPY to quaternion
        from transforms3d.euler import euler2quat
        quat = euler2quat(roll, pitch, yaw)
        target_pose.orientation.x = quat[1]
        target_pose.orientation.y = quat[2]
        target_pose.orientation. z = quat[3]
        target_pose.orientation.w = quat[0]
        
        # Plan and execute
        self.move_group.set_pose_target(target_pose)
        success = self.move_group.go(wait=True)
        
        if success:
            self. get_logger().info("Motion successful!")
        else:
            self. get_logger().error("Motion failed!")
        
        return success
    
    def move_to_joint_state(self, joint_values):
        """Move robot to specific joint configuration"""
        
        self.move_group.set_joint_value_target(joint_values)
        success = self.move_group.go(wait=True)
        
        return success

def main(args=None):
    rclpy.init(args=args)
    
    controller = MyCobotController()
    
    # Example: Move to home position
    home_joints = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    controller.move_to_joint_state(home_joints)
    
    # Example: Move to Cartesian pose
    controller.move_to_pose(0.2, 0.0, 0.3, 0.0, 0.0, 0.0)
    
    rclpy. spin(controller)
    controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__': 
    main()
```

### 4. Launch with Real Hardware

```bash
# Terminal 1: Launch robot driver
ros2 launch mycobot_description robot_bringup.launch.py

# Terminal 2: Launch MoveIt
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal 3: Launch RViz
ros2 launch mycobot_moveit_config moveit_rviz.launch. py
```

---

## Code Design

### Architecture Overview

The project follows ROS2 best practices with a modular architecture:

```
┌────────────────────────────────────────────────────────┐
│                  Application Layer                     │
│  (Custom Python/C++ nodes for specific tasks)         │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│                  MoveIt2 Layer                         │
│  ┌──────────────────────────────────────────────┐     │
│  │  Move Group Node (move_group)                │     │
│  │  - Motion planning                           │     │
│  │  - Trajectory execution                      │     │
│  │  - Scene monitoring                          │     │
│  └──────────────────────────────────────────────┘     │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│              Planning Libraries                        │
│  - OMPL (Open Motion Planning Library)                │
│  - Pilz Industrial Motion                             │
│  - CHOMP                                               │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│            Robot State & Kinematics                    │
│  - Forward/Inverse Kinematics (KDL)                   │
│  - Joint State Management                             │
│  - Transform Tree (TF2)                               │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│            Hardware Interface Layer                    │
│  - ros2_control                                        │
│  - Controller Manager                                  │
│  - Joint Trajectory Controller                        │
└────────────────┬───────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────┐
│              Hardware Drivers                          │
│  - Serial communication                                │
│  - Motor control                                       │
└────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **URDF/XACRO Files**
- Define robot kinematics and geometry
- Include visual and collision meshes
- Specify joint limits and dynamics

#### 2. **SRDF (Semantic Robot Description)**
- Define planning groups
- Specify disabled collision pairs
- Store robot poses

#### 3. **MoveIt Configuration**

**`moveit. yaml`**
```yaml
# Core MoveIt parameters
planning_plugin: ompl_interface/OMPLPlanner
request_adapters:  >-
  default_planner_request_adapters/AddTimeOptimalParameterization
  default_planner_request_adapters/FixWorkspaceBounds
  default_planner_request_adapters/FixStartStateBounds
  default_planner_request_adapters/FixStartStateCollision
  default_planner_request_adapters/FixStartStatePathConstraints
start_state_max_bounds_error: 0.1
```

**`kinematics.yaml`**
```yaml
arm: 
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.05
  kinematics_solver_attempts: 3
```

**`joint_limits.yaml`**
```yaml
joint_limits:
  joint1:
    has_velocity_limits: true
    max_velocity: 3.14
    has_acceleration_limits: true
    max_acceleration: 5.0
  # ... repeat for all joints
```

#### 4. **Launch Files**

Launch files orchestrate multiple nodes:

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("mycobot_280pi").to_dict()
    
    # Move Group Node
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config],
    )
    
    # RViz Node
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config_file],
        parameters=[moveit_config],
    )
    
    return LaunchDescription([move_group_node, rviz_node])
```

### Data Flow

```
User Input (RViz/Python API)
         │
         ▼
   Move Group Node
         │
         ├──► Planning Scene Monitor (collision checking)
         │
         ├──► Planning Pipeline
         │    ├─► OMPL Planner
         │    └─► Path Processing
         │
         ├──► Trajectory Execution Manager
         │
         ▼
  Controller Manager (ros2_control)
         │
         ▼
  Joint Trajectory Controller
         │
         ▼
   Hardware Interface
         │
         ▼
    Robot Hardware
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. **Package Not Found Error**

**Error:**
```
package 'mycobot_description' not found, searching:  [/opt/ros/jazzy]
```

**Solution:**
```bash
cd ~/grasp_workspace
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep mycobot
```

#### 2. **URDF Parse Error**

**Error:**
```
Failed to parse URDF file
```

**Solution:**
```bash
# Check URDF syntax
check_urdf ~/grasp_workspace/src/mycobot_ros2/mycobot_description/urdf/mycobot_280pi.urdf

# Validate with xacro if using . xacro files
xacro ~/grasp_workspace/src/mycobot_ros2/mycobot_description/urdf/mycobot_280pi.urdf. xacro > /tmp/test. urdf
check_urdf /tmp/test. urdf
```

#### 3. **RViz Not Showing Robot**

**Solution:**
- Check Fixed Frame is set to `base_link` or `world`
- Verify TF tree:  `ros2 run tf2_tools view_frames`
- Ensure robot_state_publisher is running

#### 4. **Planning Fails**

**Possible Causes:**
- Invalid start/goal state
- Collision detected
- Kinematic constraints violated

**Debug:**
```bash
# Check move_group logs
ros2 topic echo /move_group/display_planned_path

# Increase planning time
# In Python:
move_group.set_planning_time(10.0)
```

#### 5. **Controller Not Found**

**Error:**
```
Could not find controller: joint_trajectory_controller
```

**Solution:**
```bash
# List available controllers
ros2 control list_controllers

# Load controller
ros2 control load_controller joint_trajectory_controller
ros2 control set_controller_state joint_trajectory_controller start
```

---

## Contributing

We welcome contributions!  Here's how you can help:

### Reporting Issues

1. Check existing issues first
2. Provide detailed description
3. Include error logs and system info
4. Minimal reproducible example

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
   ```bash
   git commit -m "Add amazing feature"
   ```
6. Push and create PR
   ```bash
   git push origin feature/amazing-feature
   ```

### Code Style

- Follow ROS2 naming conventions
- Use `ament_lint` for Python/C++
- Document all public APIs
- Add unit tests for new features

```bash
# Run linting
ament_cpplint src/
ament_pep257 src/
```

---

## Roadmap

### Current Features (v1.0)
- ✅ Basic MoveIt2 configuration
- ✅ Simulation in RViz2
- ✅ Joint and Cartesian motion planning
- ✅ Collision detection

### Planned Features (v1.1)
- ⏳ Gripper control integration
- ⏳ Pick and place examples
- ⏳ Gazebo simulation support
- ⏳ Visual servoing

### Future Enhancements (v2.0)
- 🔮 Machine learning-based grasping
- 🔮 Multi-robot coordination
- 🔮 ROS2 Nav2 integration for mobile manipulation
- 🔮 Docker containerization
- 🔮 CI/CD pipeline

---

## Performance Optimization

### Tips for Better Performance

1. **Planning Time Optimization**
   ```python
   move_group.set_planning_time(5.0)  # Reduce if plans succeed consistently
   move_group.set_num_planning_attempts(10)
   ```

2. **Use Cached Plans**
   ```python
   # Store successful trajectories
   trajectory = move_group.plan()
   # Reuse later
   move_group.execute(trajectory, wait=True)
   ```

3. **Simplify Collision Geometry**
   - Use primitive shapes instead of meshes where possible
   - Reduce mesh polygon count

4. **Adjust Planner Parameters**
   ```yaml
   # In ompl_planning.yaml
   arm:
     planner_configs:
       - RRTConnect
       - RRT
     projection_evaluator:  joints(joint1,joint2)
     longest_valid_segment_fraction: 0.01  # Increase for faster planning
   ```

---

## Testing

### Unit Tests

```bash
# Run all tests
cd ~/grasp_workspace
colcon test

# View test results
colcon test-result --all --verbose
```

### Integration Tests

```bash
# Test motion planning
ros2 launch mycobot_moveit_config demo.launch.py &
ros2 run mycobot_tests test_motion_planning.py
```



**Last Updated:** 2025-12-11
