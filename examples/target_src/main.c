#include <stdint.h>
#include <stdio.h>


#ifdef _DEBUG
#include <stdio.h>
#define DBGPRINTF(format, ...) printf(format, ##__VA_ARGS__)
#else
#define DBGPRINTF(format, ...)
#endif


void TVMWrap_Init();
void *TVMWrap_GetInputPtr(int index);
void TVMWrap_Run();
void *TVMWrap_GetOutputPtr(int index);

int main()
{
    TVMWrap_Init();

    *(float*)TVMWrap_GetInputPtr(0) = 3.14f/2;

    TVMWrap_Run();

    float result;
    *(volatile float*)&result = *(float *)TVMWrap_GetOutputPtr(0);

    DBGPRINTF("out: %f\n", result);
}
