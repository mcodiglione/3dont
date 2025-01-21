cmake_minimum_required(VERSION 3.14)
project(vfuncs)

set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})

find_package(Python3 COMPONENTS Interpreter Development NumPy)
find_package(Eigen3 REQUIRED)
include(UsefulMacros)

add_library(vfuncs SHARED vfuncs.cpp)
target_link_libraries(vfuncs Eigen3::Eigen Python3::Python Python3::NumPy)
set_target_python_module_name(vfuncs)
if(WIN32)
    target_link_libraries(vfuncs ${PYTHON_LIBRARY})
elseif(APPLE)
  set_target_properties(vfuncs PROPERTIES
    LINK_FLAGS "-undefined dynamic_lookup")
elseif(UNIX)
  set_target_properties(vfuncs PROPERTIES
    LINK_FLAGS "-static-libstdc++")
endif()
target_include_directories(vfuncs PRIVATE
  ../include  # for python_util.h
)
copy_target(vfuncs)
copy_target_dependencies(vfuncs)
copy_file(__init__.py)

