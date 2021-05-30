PROJECT(tflite_wrapper)
INCLUDE(../../cmake/LinkTFLite.cmake)
ADD_LIBRARY(${PROJECT_NAME} STATIC tflite_wrapper.cc)
TARGET_LINK_LIBRARIES(${PROJECT_NAME} PUBLIC tflite tvm_static_rt)
