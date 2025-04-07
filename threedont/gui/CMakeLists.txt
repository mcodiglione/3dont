set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)

add_executable(viewer
        main.cpp
        viewer/octree.h
        viewer/box3.h
        viewer/floor_grid.h
        viewer/selection_box.h
        viewer/background.h
        viewer/look_at.h
        viewer/point_cloud.h
        viewer/viewer.h
        viewer/qt_camera.h
        viewer/camera.h
        viewer/comm_funcs.h
        viewer/opengl_funcs.h
        viewer/text.h
        viewer/camera_dolly.h
        viewer/splines.h
        viewer/point_attributes.h
        main_layout.h
        main_layout.ui
        types.h
)

# if on APPLE instead of linking to OpenGL use "-framework OpenGL"
if (APPLE)
    target_link_libraries(viewer "-framework OpenGL")
else ()
    target_link_libraries(viewer OpenGL)
endif ()


target_link_libraries(viewer Qt6::Widgets Qt6::Network Qt6::OpenGL Eigen3::Eigen ${Python_LIBRARIES})
target_include_directories(viewer PRIVATE ${Python_INCLUDE_DIRS})

install(TARGETS viewer DESTINATION threedont/viewer)

# Gui python bindings
add_library(gui MODULE
        gui_wrapper.cpp
        controller_wrapper.h
        viewer/octree.h
        viewer/box3.h
        viewer/floor_grid.h
        viewer/selection_box.h
        viewer/background.h
        viewer/look_at.h
        viewer/point_cloud.h
        viewer/viewer.h
        viewer/qt_camera.h
        viewer/camera.h
        viewer/comm_funcs.h
        viewer/opengl_funcs.h
        viewer/text.h
        viewer/camera_dolly.h
        viewer/splines.h
        viewer/point_attributes.h
        main_layout.h
        main_layout.ui
        types.h
)

if (WIN32)
    target_compile_options(gui PRIVATE /bigobj)
elseif (UNIX)
    set_target_properties(gui PROPERTIES PREFIX "")
endif ()

target_include_directories(gui PRIVATE ${Python_INCLUDE_DIRS})

if (APPLE)
    target_link_libraries(viewer "-framework OpenGL")
else ()
    target_link_libraries(viewer OpenGL)
endif ()

target_link_libraries(gui Qt6::Widgets Qt6::Network Qt6::OpenGL Eigen3::Eigen ${Python_LIBRARIES})

# install in source directory for development
if (THREEDONT_DEVELOP_BUILD)
    # send message
    message(STATUS "Installing gui in source directory for development")
    install(TARGETS gui DESTINATION ${CMAKE_SOURCE_DIR}/threedont/gui)
else ()
    install(TARGETS gui DESTINATION threedont/gui)
endif ()