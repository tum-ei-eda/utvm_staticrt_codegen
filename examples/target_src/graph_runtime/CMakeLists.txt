PROJECT(graph_runtime)

ADD_EXECUTABLE(${PROJECT_NAME}
    ${COMMON_SRCS}
    ${OUT_DIR}/runtime_wrapper.c
    ${OUT_DIR}/syslib.c
)

TARGET_INCLUDE_DIRECTORIES(${PROJECT_NAME} PUBLIC
    ${TVM_DIR}/include
    ${TVM_DIR}/3rdparty/dlpack/include
    ${TVM_DIR}/apps/bundle_deploy/crt_config
)

TARGET_LINK_LIBRARIES(${PROJECT_NAME} tvm_static_rt)
