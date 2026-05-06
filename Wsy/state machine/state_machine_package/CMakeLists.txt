cmake_minimum_required(VERSION 3.8)
project(robot_mission)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rosidl_default_generators REQUIRED)

find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(action_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/SearchTargets.srv"
  "srv/DetectBlock.srv"
  "action/ApproachTarget.action"
  "action/GraspBlock.action"
  "action/PlaceBlock.action"
  DEPENDENCIES geometry_msgs std_msgs action_msgs
)


install(PROGRAMS
  robot_mission/main_mission2_1.py
  robot_mission/vision_node.py
  robot_mission/search_object_node.py
  robot_mission/approach_object_node.py
  robot_mission/grasp_node.py
  robot_mission/place_node.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
