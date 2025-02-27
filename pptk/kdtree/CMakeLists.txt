add_library(kdtree MODULE kdtree_wrapper.cpp)

if (WIN32)
    target_compile_options(kdtree PRIVATE /bigobj)
    target_link_libraries(kdtree ${PYTHON_LIBRARY})
elseif (APPLE)
    set_target_properties(kdtree PROPERTIES
            LINK_FLAGS "-undefined dynamic_lookup")
elseif (UNIX)
    set_target_properties(kdtree PROPERTIES
            PREFIX ""
            LINK_FLAGS "-static-libstdc++")
endif ()

target_compile_definitions(kdtree PRIVATE -DUSE_TBB)
target_include_directories(kdtree PRIVATE
        ../include  # for python_util.h
        src         # for k-d tree source code
)
target_link_libraries(kdtree Python::NumPy TBB::tbb)

install(TARGETS kdtree DESTINATION pptk/kdtree)
