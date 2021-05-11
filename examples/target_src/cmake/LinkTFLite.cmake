GET_FILENAME_COMPONENT(DEFAULT_TF_DIR ../../../tensorflow REALPATH)

SET(TF_DIR "${DEFAULT_TF_DIR}" CACHE STRING "Tensorflow source directory")

GET_FILENAME_COMPONENT(TF_DIR ${TF_DIR} REALPATH)

SET(TFL_SRC ${TF_SRC}/tensorflow/lite)
SET(TFLM_SRC ${TFL_SRC}/micro)
SET(TFLD_SRC ${TFLM_SRC}/tools/make/downloads)

SET(TFLM_SRC_DEP "")
SET(TFLM_INC_DEP "")

# TFLite Micro Kernels
set(TFLM_SRC_DEP ${TFLM_SRC_DEP}
    ${TFLM_SRC}/kernels/softmax.cc
    ${TFLM_SRC}/kernels/fully_connected.cc
    ${TFLM_SRC}/kernels/pooling.cc
    ${TFLM_SRC}/kernels/add.cc
    ${TFLM_SRC}/kernels/mul.cc
    ${TFLM_SRC}/kernels/conv.cc
)

ADD_LIBRARY(tflite STATIC
    # Not really needed?
    ${TFLM_SRC}/micro_error_reporter.cc
    ${TFLM_SRC}/debug_log.cc
    ${TFLM_SRC}/micro_string.cc
    ${TFLM_SRC}/test_helpers.cc
    ${TFLM_SRC}/testing/test_utils.cc

    # For reporter->Report
    ${TF_SRC}/tensorflow/lite/core/api/error_reporter.cc

    ${TFLM_SRC_DEP}

    # Kernels
    ${TFLM_SRC}/kernels/depthwise_conv.cc
    ${TFLM_SRC}/kernels/logical.cc
    ${TFLM_SRC}/kernels/logistic.cc
    ${TFLM_SRC}/kernels/svdf.cc
    ${TFLM_SRC}/kernels/concatenation.cc
    ${TFLM_SRC}/kernels/ceil.cc
    ${TFLM_SRC}/kernels/floor.cc
    ${TFLM_SRC}/kernels/prelu.cc
    ${TFLM_SRC}/kernels/neg.cc
    ${TFLM_SRC}/kernels/elementwise.cc
    ${TFLM_SRC}/kernels/maximum_minimum.cc
    ${TFLM_SRC}/kernels/arg_min_max.cc
    ${TFLM_SRC}/kernels/reshape.cc
    ${TFLM_SRC}/kernels/comparisons.cc
    ${TFLM_SRC}/kernels/round.cc
    ${TFLM_SRC}/kernels/strided_slice.cc
    ${TFLM_SRC}/kernels/pack.cc
    ${TFLM_SRC}/kernels/pad.cc
    ${TFLM_SRC}/kernels/split.cc
    ${TFLM_SRC}/kernels/unpack.cc
    ${TFLM_SRC}/kernels/quantize.cc
    ${TFLM_SRC}/kernels/activations.cc
    ${TFLM_SRC}/kernels/dequantize.cc
    ${TFLM_SRC}/kernels/reduce.cc
    ${TFLM_SRC}/kernels/sub.cc
    ${TFLM_SRC}/kernels/resize_nearest_neighbor.cc
    ${TFLM_SRC}/kernels/l2norm.cc
    ${TFLM_SRC}/kernels/circular_buffer.cc
    ${TFLM_SRC}/kernels/ethosu.cc
    ${TFLM_SRC}/kernels/tanh.cc
    # Kernel deps
    ${TFLM_SRC}/kernels/kernel_util.cc
    ${TFLM_SRC}/all_ops_resolver.cc
    ${TFLM_SRC}/micro_utils.cc
    ${TFL_SRC}/kernels/internal/quantization_util.cc
    ${TFL_SRC}/kernels/kernel_util.cc

    ${TFL_SRC}/c/common.c
    #${TFL_SRC}/schema/schema_utils.cc

    ${TFLM_SRC}/micro_interpreter.cc
    ${TFLM_SRC}/micro_allocator.cc
    ${TFLM_SRC}/simple_memory_allocator.cc
    ${TFLM_SRC}/memory_helpers.cc
    ${TFLM_SRC}/memory_planner/greedy_memory_planner.cc
    ${TFL_SRC}/core/api/tensor_utils.cc
    ${TFL_SRC}/core/api/flatbuffer_conversions.cc
    ${TFL_SRC}/core/api/op_resolver.cc

    ${OPT_SRC}
)
TARGET_INCLUDE_DIRECTORIES(tflite PUBLIC
    ${TF_SRC}
    ${TFLD_SRC}/flatbuffers/include
    ${TFLD_SRC}/gemmlowp
    ${TFLD_SRC}/ruy
    ${TFLM_INC_DEP}
)
TARGET_COMPILE_DEFINITIONS(tflite PUBLIC
    TF_LITE_USE_GLOBAL_CMATH_FUNCTIONS
    TF_LITE_USE_GLOBAL_MAX
    TF_LITE_USE_GLOBAL_MIN
    TF_LITE_STATIC_MEMORY
    TFLITE_EMULATE_FLOAT
    "$<$<CONFIG:RELEASE>:TF_LITE_STRIP_ERROR_STRINGS>"
)
