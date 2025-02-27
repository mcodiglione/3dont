add_library(vfuncs MODULE vfuncs.cpp)
target_link_libraries(vfuncs Eigen3::Eigen Python::NumPy)

if (WIN32)
    target_link_libraries(vfuncs ${PYTHON_LIBRARY})
elseif (APPLE)
    set_target_properties(vfuncs PROPERTIES
            LINK_FLAGS "-undefined dynamic_lookup")
elseif (UNIX)
    set_target_properties(vfuncs PROPERTIES
            PREFIX ""
            LINK_FLAGS "-static-libstdc++")
endif ()
target_include_directories(vfuncs PRIVATE
        ../include  # for python_util.h
)

install(TARGETS vfuncs LIBRARY DESTINATION pptk/vfuncs)
