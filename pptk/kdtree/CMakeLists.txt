cmake_minimum_required(VERSION 3.14)
project(kdtree)

set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})

find_package(Python3 COMPONENTS Interpreter Development NumPy)

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

include(UsefulMacros)

add_library(kdtree SHARED kdtree_wrapper.cpp)
set_target_python_module_name(kdtree)
if (WIN32)
    target_compile_options(kdtree PRIVATE /bigobj)
    target_link_libraries(kdtree ${PYTHON_LIBRARY})
elseif(APPLE)
  set_target_properties(kdtree PROPERTIES
    LINK_FLAGS "-undefined dynamic_lookup")
elseif(UNIX)
  set_target_properties(kdtree PROPERTIES
    LINK_FLAGS "-static-libstdc++")
endif()
target_compile_definitions(kdtree PRIVATE -DUSE_TBB)
target_include_directories(kdtree PRIVATE
  ../include  # for python_util.h
  src         # for k-d tree source code
)
target_link_libraries(kdtree Python3::NumPy TBB::tbb)
copy_target(kdtree)
copy_target_dependencies(kdtree)
copy_file(__init__.py)

