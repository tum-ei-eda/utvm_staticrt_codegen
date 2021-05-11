CMAKE_MINIMUM_REQUIRED(VERSION 3.1 FATAL_ERROR)
PROJECT(example_target_src)

INCLUDE(../../cmake/LinkTVM.cmake)

# Enable DBGPRINTF() in DEBUG mode (`cmake -DCMAKE_BUILD_TYPE=Debug ..`)
SET(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -D_DEBUG")
SET(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -D_DEBUG")

file(GLOB KERNEL_SRCS
     ../out/kernels*.c
)

ADD_EXECUTABLE(${PROJECT_NAME}
    main.c
    ${KERNEL_SRCS}
    ../out/staticrt.c
)
TARGET_INCLUDE_DIRECTORIES(${PROJECT_NAME} PUBLIC
    ${TVM_DIR}/include
    ${TVM_DIR}/3rdparty/dlpack/include
    ${TVM_DIR}/apps/bundle_deploy/crt_config
)

IF(TFLITE_FALLBACK)
    ADD_DEFINITIONS(-DUSE_TFLITE_FALLBACK)
ENDIF()
