set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)

add_library(gui MODULE
        gui_wrapper.cpp
        controller_wrapper.cpp
        main_layout.cpp
        pointsTreeView/graph_tree_model.cpp
        pointsTreeView/graph_tree_item.cpp
        widgets/scale_legend.cpp
)

target_sources(gui PRIVATE
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

        main_layout.ui
        main_layout.h
        controller_wrapper.h
        widgets/scale_legend.h
        pointsTreeView/graph_tree_model.h
        pointsTreeView/graph_tree_item.h
)

if (WIN32)
    target_compile_options(gui PRIVATE /bigobj)
elseif (UNIX)
    set_target_properties(gui PROPERTIES PREFIX "")
endif ()

target_include_directories(gui PRIVATE ${Python_INCLUDE_DIRS})
target_link_libraries(gui Qt6::Widgets Qt6::Network Qt6::OpenGL Eigen3::Eigen ${Python_LIBRARIES})

# install in source directory for development
if (THREEDONT_DEVELOP_BUILD)
    # send message
    message(STATUS "Installing gui in source directory for development")
    install(TARGETS gui DESTINATION ${CMAKE_SOURCE_DIR}/threedont/gui)
else ()
    install(TARGETS gui DESTINATION threedont/gui)
endif ()