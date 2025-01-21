cmake_minimum_required(VERSION 3.14)
project(pptk)

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})

# localize all dependencies (.dll, .so, or .dylib) in the following folder
set(PPTK_LIBS_DIR ${PROJECT_BINARY_DIR}/pptk/libs)

# use patchelf to modify binary RPATH when building pptk on Linux
if(UNIX AND NOT APPLE)
  find_program(PPTK_PATCHELF patchelf)
  if (NOT PPTK_PATCHELF)
    message(FATAL_ERROR
      "patchelf needed for localizing library dependencies; \
      please manually set the PPTK_PATCHELF variable.")
  endif()
endif()

# adds -std=gnu++11 flag when compiling with gcc
set(CMAKE_CXX_STANDARD 11)

include(UsefulMacros)

# following lines specifies the CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS variable
set(CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS_SKIP TRUE)
set(CMAKE_INSTALL_OPENMP_LIBRARIES TRUE)  # requires cmake 3.1
include(InstallRequiredSystemLibraries)

copy_file(setup.py)
copy_file(LICENSE)
add_subdirectory(pptk)
add_subdirectory(licenses)
