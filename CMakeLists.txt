cmake_minimum_required(VERSION 3.15)
project(pptk)

# set(CMAKE_BUILD_TYPE Release)

# Qt5::QXcbGlxIntegrationPlugin
# Qt5::QXcbIntegrationPlugin

# localize all dependencies (.dll, .so, or .dylib) in the following folder
set(PPTK_LIBS_DIR ${PROJECT_BINARY_DIR}/pptk/libs)

# adds -std=gnu++11 flag when compiling with gcc
set(CMAKE_CXX_STANDARD 11)


find_package(OpenMP REQUIRED)
find_package(OpenGL REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(Qt5 CONFIG REQUIRED COMPONENTS Widgets Network OpenGL Core)
find_package(Python COMPONENTS Interpreter Development.Module NumPy)

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


add_subdirectory(pptk)
add_subdirectory(licenses)
