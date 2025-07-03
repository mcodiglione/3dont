set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)

add_library(gui MODULE
        gui_wrapper.cpp
        controller_wrapper.cpp
        main_layout.cpp
        points_tree_view/graph_tree_model.cpp
        points_tree_view/graph_tree_item.cpp
        widgets/scale_legend.cpp
)

target_sources(gui PRIVATE
        viewer/viewer.h
        main_layout.ui
        main_layout.h
        widgets/scale_legend.h
        points_tree_view/graph_tree_model.h
        dialogs/properties_mapping_selection.h
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