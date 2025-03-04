set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)

add_executable(viewer
        main.cpp
        octree.h
        box3.h
        floor_grid.h
        selection_box.h
        background.h
        look_at.h
        point_cloud.h
        viewer.h
        qt_camera.h
        camera.h
        comm_funcs.h
        opengl_funcs.h
        text.h
        camera_dolly.h
        splines.h
        point_attributes.h
        main_layout.h
        main_layout.ui
)

target_link_libraries(viewer OpenGL Qt6::Widgets Qt6::Network Qt6::OpenGL Eigen3::Eigen Python::NumPy)
target_include_directories(viewer PRIVATE)

install(TARGETS viewer DESTINATION threedont/viewer)

# Gui python bindings
add_library(gui MODULE
        gui_wrapper.cpp
        octree.h
        box3.h
        floor_grid.h
        selection_box.h
        background.h
        look_at.h
        point_cloud.h
        viewer.h
        qt_camera.h
        camera.h
        comm_funcs.h
        opengl_funcs.h
        text.h
        camera_dolly.h
        splines.h
        point_attributes.h
        main_layout.h
        main_layout.ui
)

if (WIN32)
    target_compile_options(gui PRIVATE /bigobj)
elseif (APPLE)
    set_target_properties(gui PROPERTIES
            LINK_FLAGS "-undefined dynamic_lookup")
elseif (UNIX)
    set_target_properties(gui PROPERTIES PREFIX "")
endif ()

target_include_directories(gui PRIVATE ${Python_INCLUDE_DIRS})

target_link_libraries(gui OpenGL Qt6::Widgets Qt6::Network Qt6::OpenGL Eigen3::Eigen ${Python_LIBRARIES})

install(TARGETS gui DESTINATION threedont/gui)
