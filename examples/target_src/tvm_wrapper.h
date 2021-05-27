#ifndef TVM_WRAPPER_H
#define TVM_WRAPPER_H

#include <stddef.h>

void TVMWrap_Init();
void *TVMWrap_GetInputPtr(int index);
size_t TVMWrap_GetInputSize(int index);
void TVMWrap_Run();
void *TVMWrap_GetOutputPtr(int index);
size_t TVMWrap_GetOutputSize(int index);

#endif  // TVM_WRAPPER_H
