# Mission 2.1 ROS 2 State Machine

This package completes `main_mission2_1.py` and adds the minimum service/action interfaces and mock nodes needed to test the mission flow.

## Files

```text
robot_mission/
├── robot_mission/
│   ├── main_mission2_1.py
│   ├── vision_node.py
│   ├── search_object_node.py
│   ├── approach_object_node.py
│   ├── grasp_node.py
│   └── place_node.py
├── srv/
│   ├── SearchTargets.srv
│   └── DetectBlock.srv
├── action/
│   ├── ApproachTarget.action
│   ├── GraspBlock.action
│   └── PlaceBlock.action
├── CMakeLists.txt
└── package.xml
```

## Build

Place `robot_mission` under `ros2_ws/src`, then run:

```bash
cd ~/ros2_ws
colcon build --packages-select robot_mission
source install/setup.bash
```

## Run mock nodes

```bash
ros2 run robot_mission search_object_node.py
ros2 run robot_mission vision_node.py
ros2 run robot_mission approach_object_node.py
ros2 run robot_mission grasp_node.py
ros2 run robot_mission place_node.py
```

## Run state machine

The provided `main()` currently uses mock mode:

```python
sm = RobotStateMachine(use_mock_modules=True)
```

After custom services/actions and nodes are ready, change it to:

```python
sm = RobotStateMachine(use_mock_modules=False)
```

Then run:

```bash
ros2 run robot_mission main_mission2_1.py
```
