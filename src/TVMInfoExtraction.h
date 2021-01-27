#ifndef TVM_COMPILER_WRAP_H
#define TVM_COMPILER_WRAP_H

#include <stddef.h>
#include <stdint.h>

typedef struct Storage_Info
{
    void *buffer;
    size_t size;
    uint8_t *static_data;
} Storage_Info;

typedef struct Arg_Info
{
    void *data;
    ptrdiff_t offset;
    size_t dataSize;
    Storage_Info *storage;
} Arg_Info;

typedef struct Op_Info
{
    int active;
    char name[120];
    int numArgs;
    Arg_Info *args;
} Op_Info;

typedef struct Graph_Info
{
    int numOps;
    Op_Info *ops;
    int numStorages;
    Storage_Info **storages;
    int numInputs;
    Arg_Info **inputs;
    int numOutputs;
    Arg_Info **outputs;
} Graph_Info;

#ifdef __cplusplus

extern "C" {
void *create_tvm_rt(const char *json_data, const char *params_data, uint64_t params_size);
Graph_Info *extract_graph_info(void *grt, const char *params_data, uint64_t params_size);
}

#endif

#endif
