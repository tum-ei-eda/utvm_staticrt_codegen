#include <stdint.h>
#include <stdio.h>

#include "tvm/runtime/c_runtime_api.h"


#ifdef _DEBUG
#include <stdio.h>
#define DBGPRINTF(format, ...) printf(format, ##__VA_ARGS__)
#else
#define DBGPRINTF(format, ...)
#endif


#include <tvm/runtime/crt/packed_func.h>
TVMModuleHandle TVMArgs_AsModuleHandle(const TVMArgs* args, size_t index);


void TVMWrap_Init();
void *TVMWrap_GetInputPtr(int index);
void TVMWrap_Run();
void *TVMWrap_GetOutputPtr(int index);


void TVMPlatformAbort(tvm_crt_error_t e) { exit(1); }

#ifdef USE_TFLITE_FALLBACK
int32_t tflite_extern_wrapper(TVMValue* args, int* type_code,
                                     int num_args, TVMValue* out_value,
                                     int* out_type_code);
#endif  // USE_TFLITE_FALLBACK

int main()
{
    TVMWrap_Init();

    *(float*)TVMWrap_GetInputPtr(0) = 3.14f/2;

#ifdef USE_TFLITE_FALLBACK
    TVMFuncRegisterGlobal(
    //"tvm.runtime.tflite_custom_op",
    "tvm.runtime.tflite_extern_wrapper",
    (TVMFunctionHandle)&tflite_extern_wrapper, 0);
#endif  // USE_TFLITE_FALLBACK

    TVMWrap_Run();

    float result;
    *(volatile float*)&result = *(float *)TVMWrap_GetOutputPtr(0);

    DBGPRINTF("out: %f\n", result);
}
