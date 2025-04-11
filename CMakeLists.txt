cmake_minimum_required(VERSION 3.15)
project(threedont)

# set(CMAKE_BUILD_TYPE Release)

# Qt5::QXcbGlxIntegrationPlugin
# Qt5::QXcbIntegrationPlugin

# adds -std=gnu++11 flag when compiling with gcc
set(CMAKE_CXX_STANDARD 11)

option(THREEDONT_DEVELOP_BUILD "Enable development build" OFF)

find_package(OpenMP REQUIRED)
find_package(OpenGL REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(Qt6 CONFIG REQUIRED COMPONENTS Widgets Network OpenGL Core)
find_package(Python COMPONENTS Interpreter Development REQUIRED)

add_subdirectory(threedont)
add_subdirectory(licenses)
