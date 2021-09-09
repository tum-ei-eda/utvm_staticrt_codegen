SET(DEFAULT_TVM_DIR ../tvm)
GET_FILENAME_COMPONENT(DEFAULT_TVM_DIR ${DEFAULT_TVM_DIR} REALPATH)

SET(TVM_DIR "${DEFAULT_TVM_DIR}" CACHE STRING "TVM source directory")

GET_FILENAME_COMPONENT(TVM_DIR ${TVM_DIR} REALPATH)

ADD_LIBRARY(tvm_static_rt STATIC
    ${TVM_DIR}/apps/bundle_deploy/bundle_static.c

    ${TVM_DIR}/src/runtime/crt/common/crt_backend_api.c
    ${TVM_DIR}/src/runtime/crt/common/crt_runtime_api.c
    ${TVM_DIR}/src/runtime/crt/common/func_registry.c
    ${TVM_DIR}/src/runtime/crt/common/ndarray.c
    ${TVM_DIR}/src/runtime/crt/common/packed_func.c
    ${TVM_DIR}/src/runtime/crt/memory/page_allocator.c
    ${TVM_DIR}/src/runtime/crt/memory/stack_allocator.c
    ${TVM_DIR}/src/runtime/crt/graph_executor/graph_executor.c
    ${TVM_DIR}/src/runtime/crt/graph_executor/load_json.c
)
TARGET_INCLUDE_DIRECTORIES(tvm_static_rt PUBLIC
    ${TVM_DIR}/include
    ${TVM_DIR}/3rdparty/dlpack/include
    ${TVM_DIR}/apps/bundle_deploy
    ${TVM_DIR}/src/runtime/crt/include
)

IF(TVM_CRT_CONFIG_DIR)
    TARGET_INCLUDE_DIRECTORIES(tvm_static_rt PUBLIC
        ${TVM_CRT_CONFIG_DIR}
    )
ELSE()
    TARGET_INCLUDE_DIRECTORIES(tvm_static_rt PUBLIC
        ${TVM_DIR}/apps/bundle_deploy/crt_config
    )
ENDIF()
