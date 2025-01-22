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


target_compile_definitions(estimate_normals PRIVATE -DUSE_TBB)
target_link_libraries(estimate_normals Python::NumPy Eigen3::Eigen TBB::tbb)
target_include_directories(estimate_normals PRIVATE
  ../include     # for python_util.h
  ../kdtree/src  # for kdtree.h
)

install(TARGETS estimate_normals LIBRARY DESTINATION pptk/estimate_normals)