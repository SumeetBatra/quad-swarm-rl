cmake_minimum_required(VERSION 3.4)
project(c_network_project LANGUAGES CXX)

add_subdirectory(pybind11)
pybind11_add_module(c_network c_network.cpp)
