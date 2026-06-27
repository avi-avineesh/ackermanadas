cmake_minimum_required(VERSION 3.8)
project(robot_bringup)
find_package(ament_cmake REQUIRED)
install(DIRECTORY urdf meshes worlds launch DESTINATION share/${PROJECT_NAME}/)
install(PROGRAMS scripts/spawn_ego.py RENAME spawn_ego
        DESTINATION lib/${PROJECT_NAME})
ament_package()
