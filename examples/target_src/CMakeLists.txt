CMAKE_MINIMUM_REQUIRED(VERSION 3.1 FATAL_ERROR)
PROJECT(example_target_src)

INCLUDE(../../cmake/LinkTVM.cmake)


ADD_EXECUTABLE(${PROJECT_NAME}
    main.c
    ../out/kernels.c
    ../out/staticrt.c
)
TARGET_INCLUDE_DIRECTORIES(${PROJECT_NAME} PUBLIC
    ${TVM_DIR}/include
    ${TVM_DIR}/3rdparty/dlpack/include
    ${TVM_DIR}/apps/bundle_deploy/crt_config
)
