#include <stdio.h>
//#include <stdint.h>

#include "tvm/runtime/c_runtime_api.h"
//#include "tvm/runtime/data_type.h"
//#include "tvm/runtime/crt/packed_func.h"

#include "tensorflow/lite/c/common.h"
#include "tensorflow/lite/c/builtin_op_data.h"
#include "tensorflow/lite/micro/micro_utils.h"
#include "tensorflow/lite/micro/kernels/micro_ops.h"
//#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
//#include "tensorflow/lite/schema/schema_generated.h"

#ifdef _DEBUG
#include <stdio.h>
#define DBGPRINTF(format, ...) printf(format, ##__VA_ARGS__)
#else
#define DBGPRINTF(format, ...)
#endif


#if defined __GNUC__
#define ALIGN(X) __attribute__((aligned(X)))
#elif defined _MSC_VER
#define ALIGN(X) __declspec(align(X))
#elif defined __TASKING__
#define ALIGN(X) __align(X)
#endif

extern "C" void test() {
    TfLiteAddParams p_ref = {kTfLiteActSigmoid, true};
    size_t size = sizeof(p_ref);
    printf("\nSIZE_REF=%lu\n", sizeof(p_ref));
    printf("SIZE_REF=%lu\n", sizeof(p_ref.activation));
    printf("SIZE_REF=%lu\n", sizeof(p_ref.pot_scale_int16));
    for (int i = 0 ; i < size ; i++) {
        printf("%d ", ((char*)&p_ref)[i]);
    }
    char x[8] = {0x06, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00};
    char* y = x;
    TfLiteAddParams p = *(TfLiteAddParams*)x;
    printf("Act: %d", p.activation);
    printf("Pot: %d", p.pot_scale_int16);
    TfLiteFullyConnectedParams ppp = {kTfLiteActSigmoid, kTfLiteFullyConnectedWeightsFormatShuffled4x16Int8, true, true};
    size = sizeof(ppp);
    printf("\nSIZE=%lu\n", size);
    printf("SIZE=%lu\n", sizeof(ppp.activation));
    printf("SIZE=%lu\n", sizeof(ppp.weights_format));
    printf("SIZE=%lu\n", sizeof(ppp.keep_num_dims));
    printf("SIZE=%lu\n", sizeof(ppp.asymmetric_quantize_inputs));
    for (int i = 0 ; i < size ; i++) {
        printf("%d ", ((char*)&ppp)[i]);
    }
}

namespace tvm {
namespace runtime {
TfLiteType DLDataType2TfLiteType(const DLDataType* dtype) {
  if (dtype->lanes != 1) {
  }
  switch (dtype->code) {
    case kDLInt:
      if (dtype->bits == 8) {
        return kTfLiteInt8;
      } else if (dtype->bits == 16) {
        return kTfLiteInt16;
      } else if (dtype->bits == 32) {
        return kTfLiteInt32;
      } else if (dtype->bits == 64) {
        return kTfLiteInt64;
      } else {
        // TODO: Handle Error at the End!
      }
      break;
    case kDLUInt:
      if (dtype->bits == 8) {
        return kTfLiteUInt8;
      } else {
        // TODO: Handle Error at the End!
      }
      break;
    case kDLFloat:
      if (dtype->bits == 16) {
        return kTfLiteFloat16;
      } else if (dtype->bits == 32) {
        return kTfLiteFloat32;
      } else {
        // TODO: Handle Error at the End!
      }
      break;
    default:
      break;
  }
  return kTfLiteFloat32;
}

tflite::ErrorReporter* error_reporter = nullptr;
class DummyReporter : public tflite::ErrorReporter {
 public:
  ~DummyReporter() {}
  int Report(const char*, va_list) override { return 0; }

 private:
  TF_LITE_REMOVE_VIRTUAL_DELETE
};

inline TfLiteTensor DLTensor2TfLiteTensor(const DLTensor* tensor) {
  TfLiteType dtype_converted = DLDataType2TfLiteType(&tensor->dtype);
  TfLiteTensor tensor_converted;
  tensor_converted.type = dtype_converted;
  tensor_converted.data.raw =
      reinterpret_cast<char*>(const_cast<void*>(tensor->data));
  // TfLiteIntArray* shape_array = TfLiteIntArrayCreate(tensor->ndim); // TODO:
  // malloc not allowed beause of static memory flag set!
  TfLiteIntArray* shape_array =
      (TfLiteIntArray*)malloc(TfLiteIntArrayGetSizeInBytes(tensor->ndim));
  shape_array->size = tensor->ndim;
  for (size_t dim_index = 0; dim_index < tensor->ndim; dim_index++) {
    shape_array->data[dim_index] = tensor->shape[dim_index];
  }
  tensor_converted.dims = shape_array;
  tensor_converted.bytes = tflite::ElementCount(*shape_array) * sizeof(float);
  tensor_converted.is_variable = false;  // TODO: ?
  if (tensor->strides != NULL) {
    // TODO: handle error!
  }
  return tensor_converted;
}


constexpr int kTensorArenaSize = 300;
uint8_t tensor_arena[kTensorArenaSize] ALIGN(16);

static void* AllocatePersistentBuffer(struct TfLiteContext* ctx, size_t bytes) {
  static uint8_t* AllocPtr = tensor_arena + sizeof(tensor_arena);

  AllocPtr -= bytes;
  return AllocPtr;
}

TfLiteEvalTensor evalTensors[10]; // TODO: do not hardcode

static TfLiteEvalTensor* GetEvalTensor(const struct TfLiteContext* context,
                                       int tensor_idx) {
  return &evalTensors[tensor_idx];
}

extern "C" int32_t tflite_extern_wrapper(TVMValue* args, int* type_code,
                                     int num_args, TVMValue* out_value,
                                     int* out_type_code) {
    char* op_name = (char*)args[0].v_handle;
    char is_builtin = (args[1].v_int64 != 0);
    is_builtin = 1; // TODO
    DBGPRINTF("\nOP=%s | IS_BUILTIN=%d\n", op_name, is_builtin);
    int64_t input_tensors_size = args[2].v_int64;
    int64_t output_tensors_size = args[3].v_int64;
    int64_t tensors_size = input_tensors_size + output_tensors_size;

    DLTensor *options_tensor = (DLTensor*)args[4+input_tensors_size+output_tensors_size].v_handle;
    int s = options_tensor->shape[0];
    DBGPRINTF("OPTIONS: ");
    for ( int i = 0 ; i < s ; i++ ) {
        DBGPRINTF("%d,", ((char*)options_tensor->data)[i]);
    }
    DBGPRINTF("\n");

    std::vector<TfLiteTensor> tensors_converted(input_tensors_size+output_tensors_size);

    for (size_t index = 0; index < input_tensors_size; index++) {
      DLTensor* tensor = (DLTensor*)args[4 + index].v_handle;
      TfLiteTensor tensor_converted = DLTensor2TfLiteTensor(tensor);
      tensors_converted[index] = tensor_converted;
    }
    for (size_t index = 0; index < output_tensors_size; index++) {
      DLTensor* tensor = (DLTensor*)args[4 + input_tensors_size + index].v_handle;
      TfLiteTensor tensor_converted = DLTensor2TfLiteTensor(tensor);
      tensors_converted[input_tensors_size + index] = tensor_converted;
    }

    for(size_t i = 0; i < tensors_size; ++i) {
      evalTensors[i].data.data = tensors_converted[i].data.data;
      evalTensors[i].type = tensors_converted[i].type;
      evalTensors[i].dims = tensors_converted[i].dims;
    }

    TfLiteContext context;
    context.tensors_size = tensors_size;
    context.tensors = tensors_converted.data();
    context.recommended_num_threads = 1;
    context.GetEvalTensor = GetEvalTensor;
    context.AllocatePersistentBuffer = AllocatePersistentBuffer;  // TODO: implement!
    static tflite::MicroMutableOpResolver<1> resolver(error_reporter);
    /*if (resolver.AddAdd() != kTfLiteOk) {
      return -1;
    }*/
    if (resolver.AddFullyConnected() != kTfLiteOk) {
      return -1;
    }

    /*const TfLiteRegistration* registration = resolver.FindOp("Add2"); 
    if (!registration) {
      return -1;
    }*/
    const TfLiteRegistration* registration = resolver.FindOp(tflite::BuiltinOperator_FULLY_CONNECTED);
    if (!registration) {
      return -1;
    }

    void* builtin_data;
    const char* init_data;
    const void* custom_initial_data;
    int custom_initial_data_size;
    if (is_builtin) {
      builtin_data = (void*)options_tensor->data;
      init_data = (const char*)builtin_data;
      custom_initial_data = nullptr;
      custom_initial_data_size = 0;
    } else { // CUSTOM
      builtin_data = nullptr; // TODO
      init_data = nullptr; // TODO
      custom_initial_data = nullptr; // TODO
      custom_initial_data_size = 0; // TODO
    }
    const size_t init_data_size = 0; // TODO: ?
    void* user_data = nullptr;

    if (registration->init) {
      user_data = registration->init(&context, init_data, init_data_size);
    }

    TfLiteIntArray* inputs_array = (TfLiteIntArray*)malloc(
        TfLiteIntArrayGetSizeInBytes(input_tensors_size));
    inputs_array->size = input_tensors_size;
    //inputs_array->data[0] = input_tensors_size;
    for (size_t index = 0; index < input_tensors_size; index++) {
      inputs_array->data[index] = index;
    }
    TfLiteIntArray* outputs_array = (TfLiteIntArray*)malloc(
        TfLiteIntArrayGetSizeInBytes(output_tensors_size));
    outputs_array->size = output_tensors_size;
    //outputs_array->data[0] = output_tensors_size;
    for (size_t index = 0; index < output_tensors_size; index++) {
      outputs_array->data[index] = input_tensors_size + index;
    }

    TfLiteNode node;
    node.inputs = inputs_array;
    node.outputs = outputs_array;
    //node.temporaries = temporaries_array; // TODO: ?
    //node.intermediates = intermediates_array; // TODO: ?
    node.user_data = user_data;
    //node.builtin_data = reinterpret_cast<void*>(&builtin_data);
    node.builtin_data = reinterpret_cast<void*>(builtin_data);
    node.custom_initial_data = nullptr;
    node.custom_initial_data_size = 0;
    //node.delegate = nullptr;

    if (registration->prepare) {
      if (registration->prepare(&context, &node) != kTfLiteOk) {
        return -1;
      }
    }

    if (!registration->invoke) {
      return -1;
    }
    if (registration->invoke(&context, &node) != kTfLiteOk) {
      return -1;
    }

    if (registration->free) {
      registration->free(&context, user_data);
    }

    return 0;
}

}  // namespace runtime
}  // namespace tvm
