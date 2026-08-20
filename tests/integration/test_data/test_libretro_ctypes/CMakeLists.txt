cmake_minimum_required(VERSION 3.5)
project(libretro_test LANGUAGES C)

# The same source built three ways, one per settings API a core can use
add_library(${PROJECT_NAME} SHARED libretro.c)
set_target_properties(${PROJECT_NAME} PROPERTIES PREFIX "")

add_library(${PROJECT_NAME}_variables SHARED libretro.c)
set_target_properties(${PROJECT_NAME}_variables PROPERTIES PREFIX "")
target_compile_definitions(${PROJECT_NAME}_variables PRIVATE TEST_CORE_VARIABLES)

add_library(${PROJECT_NAME}_init SHARED libretro.c)
set_target_properties(${PROJECT_NAME}_init PROPERTIES PREFIX "")
target_compile_definitions(${PROJECT_NAME}_init PRIVATE TEST_CORE_INIT)
