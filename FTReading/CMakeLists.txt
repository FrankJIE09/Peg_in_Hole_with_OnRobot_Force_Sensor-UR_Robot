project(FTReading)
cmake_minimum_required(VERSION 2.8)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CONFIGURATION_TYPES "Release")

find_package(pybind11)
INCLUDE_DIRECTORIES(${pybind11_INCLUDE_DIRS})

aux_source_directory(./src SRC_LIST)
pybind11_add_module(FTReading  ${SRC_LIST})


