SET(DEFAULT_TVM_DIR ../tvm)
GET_FILENAME_COMPONENT(DEFAULT_TVM_DIR ${DEFAULT_TVM_DIR} REALPATH)
SET(TVM_DIR "${DEFAULT_TVM_DIR}" CACHE STRING "TVM source directory")
GET_FILENAME_COMPONENT(TVM_DIR ${TVM_DIR} REALPATH)

SET(TVM_ALIGNMENT_BYTES 1)

SET(TVM_HEADERS
    ${TVM_DIR}/include
    ${TVM_DIR}/3rdparty/dlpack/include
    ${TVM_DIR}/apps/bundle_deploy
    ${TVM_DIR}/apps/bundle_deploy/crt_config
    ${TVM_DIR}/src/runtime/crt/include
)

ADD_LIBRARY(tvm_rt STATIC
    ${TVM_DIR}/apps/bundle_deploy/bundle_static.c
    ${TVM_DIR}/src/runtime/crt/common/crt_backend_api.c
    ${TVM_DIR}/src/runtime/crt/common/crt_runtime_api.c
    ${TVM_DIR}/src/runtime/crt/common/func_registry.c
    ${TVM_DIR}/src/runtime/crt/memory/page_allocator.c
    ${TVM_DIR}/src/runtime/crt/common/ndarray.c
    ${TVM_DIR}/src/runtime/crt/common/packed_func.c
    ${TVM_DIR}/src/runtime/crt/graph_executor/graph_executor.c
    ${TVM_DIR}/src/runtime/crt/graph_executor/load_json.c
)
TARGET_INCLUDE_DIRECTORIES(tvm_rt PUBLIC
    ${TVM_HEADERS}
)
TARGET_COMPILE_DEFINITIONS(tvm_rt PUBLIC
    -DTVM_RUNTIME_ALLOC_ALIGNMENT_BYTES=${TVM_ALIGNMENT_BYTES}
)

ADD_LIBRARY(tvm_static_rt STATIC
    ${TVM_DIR}/src/runtime/crt/common/crt_runtime_api.c
    ${TVM_DIR}/src/runtime/crt/memory/stack_allocator.c
)
TARGET_INCLUDE_DIRECTORIES(tvm_static_rt PUBLIC
    ${TVM_HEADERS}
)
TARGET_COMPILE_DEFINITIONS(tvm_static_rt PUBLIC
    -DTVM_RUNTIME_ALLOC_ALIGNMENT_BYTES=${TVM_ALIGNMENT_BYTES}
)

ADD_LIBRARY(tvm_graph_rt STATIC
    ${TVM_DIR}/apps/bundle_deploy/bundle_static.c
    ${TVM_DIR}/src/runtime/crt/common/crt_backend_api.c
    ${TVM_DIR}/src/runtime/crt/common/crt_runtime_api.c
    ${TVM_DIR}/src/runtime/crt/common/func_registry.c
    ${TVM_DIR}/src/runtime/crt/memory/page_allocator.c
    ${TVM_DIR}/src/runtime/crt/common/ndarray.c
    ${TVM_DIR}/src/runtime/crt/common/packed_func.c
    ${TVM_DIR}/src/runtime/crt/graph_executor/graph_executor.c
    ${TVM_DIR}/src/runtime/crt/graph_executor/load_json.c
)
TARGET_INCLUDE_DIRECTORIES(tvm_graph_rt PUBLIC
    ${TVM_HEADERS}
)
TARGET_COMPILE_DEFINITIONS(tvm_graph_rt PUBLIC
    -DTVM_RUNTIME_ALLOC_ALIGNMENT_BYTES=${TVM_ALIGNMENT_BYTES}
)

ADD_LIBRARY(tvm_aot_rt STATIC
    ${TVM_DIR}/src/runtime/crt/common/crt_backend_api.c
    ${TVM_DIR}/src/runtime/crt/memory/stack_allocator.c
    ${TVM_DIR}/src/runtime/crt/aot_executor/aot_executor.c
)
TARGET_INCLUDE_DIRECTORIES(tvm_aot_rt PUBLIC
    ${TVM_HEADERS}
)
TARGET_COMPILE_DEFINITIONS(tvm_aot_rt PUBLIC
    -DTVM_RUNTIME_ALLOC_ALIGNMENT_BYTES=${TVM_ALIGNMENT_BYTES}
)
