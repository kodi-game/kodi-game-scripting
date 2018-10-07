cmake_minimum_required(VERSION 3.1)
project(libretro_test LANGUAGES C)

add_library(${PROJECT_NAME} SHARED libretro.c)
set_target_properties(${PROJECT_NAME} PROPERTIES PREFIX "")
