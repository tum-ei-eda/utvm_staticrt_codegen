#include <stdint.h>
#include <stdio.h>
#include <tvm/runtime/crt/error_codes.h>

#include "tvm_wrapper.h"
#include "printing.h"

void TVMPlatformAbort(tvm_crt_error_t code);

int main()
{
    TVMWrap_Init();

    *(float*)TVMWrap_GetInputPtr(0) = 3.14f/2;

    TVMWrap_Run();

    float result;
    *(volatile float*)&result = *(float *)TVMWrap_GetOutputPtr(0);

    DBGPRINTF("out: %f\n", result);
}
