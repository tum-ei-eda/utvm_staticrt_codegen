GET_FILENAME_COMPONENT(TVM_TRY_PATH ../../../tvm REALPATH)
IF(EXISTS ${TVM_TRY_PATH})
    SET(DEFAULT_TVM_DIR ${TVM_TRY_PATH})
ELSE()
    SET(DEFAULT_TVM_DIR ../tvm)
ENDIF()

SET(TVM_DIR "${DEFAULT_TVM_DIR}" CACHE STRING "TVM source directory")

GET_FILENAME_COMPONENT(TVM_DIR ${TVM_DIR} REALPATH)

ADD_LIBRARY(tvm_static_rt STATIC
    ${TVM_DIR}/apps/bundle_deploy/bundle_static.c

    ${TVM_DIR}/src/runtime/crt/common/crt_backend_api.c
    ${TVM_DIR}/src/runtime/crt/common/crt_runtime_api.c
    ${TVM_DIR}/src/runtime/crt/common/func_registry.c
    ${TVM_DIR}/src/runtime/crt/common/ndarray.c
    ${TVM_DIR}/src/runtime/crt/common/packed_func.c
    ${TVM_DIR}/src/runtime/crt/memory/memory.c
    ${TVM_DIR}/src/runtime/crt/graph_executor/graph_executor.c
    ${TVM_DIR}/src/runtime/crt/graph_executor/load_json.c
)
TARGET_INCLUDE_DIRECTORIES(tvm_static_rt PUBLIC
    ${TVM_DIR}/include
    ${TVM_DIR}/3rdparty/dlpack/include
    ${TVM_DIR}/apps/bundle_deploy
    ${TVM_DIR}/apps/bundle_deploy/crt_config
    ${TVM_DIR}/src/runtime/crt/include
)
