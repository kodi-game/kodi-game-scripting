cmake_minimum_required(VERSION 3.1)
project(game.libretro.mygame)

list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR})

find_package(Kodi REQUIRED)
find_library(MYGAME_LIB NAMES ${CMAKE_SHARED_LIBRARY_SUFFIX} PATH_SUFFIXES libretro)

set(MYGAME_CUSTOM_BINARY ${MYGAME_LIB}
    ${PROJECT_NAME}${CMAKE_SHARED_LIBRARY_SUFFIX})

build_addon(${PROJECT_NAME} MYGAME "")

include(CPack)
