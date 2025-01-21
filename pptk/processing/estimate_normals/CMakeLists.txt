cmake_minimum_required(VERSION 3.14)
project(estimate_normals)

set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})

find_package(Python3 COMPONENTS Interpreter Development NumPy)
find_package(Eigen3 REQUIRED)

find_package(TBB COMPONENTS tbb)  
if(NOT TBB_FOUND)
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(TBB REQUIRED tbb)
  
  add_library(TBB::tbb INTERFACE IMPORTED)
  set_target_properties(TBB::tbb PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${TBB_INCLUDE_DIRS}"
    INTERFACE_LINK_LIBRARIES "${TBB_LIBRARIES}"
  )
endif()

find_package(OpenMP REQUIRED)
include(UsefulMacros)

add_library(estimate_normals SHARED estimate_normals.cpp)
set(_link_flags ${OpenMP_CXX_FLAGS})
if(WIN32)
  target_link_libraries(estimate_normals ${PYTHON_LIBRARY})
elseif(APPLE)
  set(_link_flags "${_link_flags} -undefined dynamic_lookup")
elseif(UNIX)
  set(_link_flags "${_link_flags} -static-libstdc++")
endif()
set_target_properties(estimate_normals PROPERTIES
  COMPILE_FLAGS ${OpenMP_CXX_FLAGS}
  LINK_FLAGS ${_link_flags})
set_target_python_module_name(estimate_normals)
target_compile_definitions(estimate_normals PRIVATE -DUSE_TBB)
target_link_libraries(estimate_normals Python3::NumPy Eigen3::Eigen TBB::tbb)
target_include_directories(estimate_normals PRIVATE
  ../../include     # for python_util.h
  ../../kdtree/src  # for kdtree.h
)
copy_target(estimate_normals)
copy_target_dependencies(estimate_normals)
copy_file(__init__.py)

