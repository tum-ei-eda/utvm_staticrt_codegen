#include "TVMInfoExtraction.h"

#include "tvm/runtime/crt/internal/graph_runtime/graph_runtime.h"
#include "tvm/runtime/crt/crt.h"
#include "tvm/runtime/crt/packed_func.h"
#include "tvm/runtime/crt/memory.h"
#include "bundle.h"

#include <stdbool.h>


const TVMModule* TVMSystemLibEntryPoint(void) {
    return NULL;
}
TVMModuleHandle TVMArgs_AsModuleHandle(const TVMArgs* args, size_t index);


void *create_tvm_rt(const char *json_data, const char *params_data, uint64_t params_size)
{
    return (TVMGraphRuntime*)tvm_runtime_create(json_data, params_data, params_size, NULL);
}

static size_t GetTensorSize(const DLTensor *t)
{
    size_t sz = 1;
    for (tvm_index_t i = 0; i < t->ndim; i++) {
        sz *= t->shape[i];
    }
    sz *= (t->dtype.bits * t->dtype.lanes + 7) / 8;
    return sz;
}
uint32_t TVMGraphRuntime_GetEntryId(TVMGraphRuntime *, uint32_t, uint32_t);

// See: TVMGraphRuntime_LoadParams
static uint32_t *GetStaticInputEIDs(size_t *numReturned, TVMGraphRuntime *g, const char *params_data, uint64_t params_size)
{
    const uint8_t *p = params_data;

    // Header
    p += sizeof(uint64_t);
    // Reserved
    p += sizeof(uint64_t);

    // Names
    uint64_t numNames = *(uint64_t*)p;
    p += sizeof(numNames);
    char **names = malloc(numNames * sizeof(char*));
    uint32_t *out = malloc(numNames * sizeof(uint32_t));
    for (int i = 0; i < numNames; i++)
    {
        // Name length
        uint64_t nameLen = *(uint64_t*)p;
        p += sizeof(nameLen);

        names[i] = malloc((nameLen + 1) * sizeof(char));
        memcpy(names[i], p, nameLen);
        names[i][nameLen] = '\0';
        p += nameLen;

        int32_t inIndex = TVMGraphRuntime_GetInputIndex(g, names[i]);
        out[i] = TVMGraphRuntime_GetEntryId(g, g->input_nodes[inIndex], 0);

        free(names[i]);
    }
    free(names);

    *numReturned = numNames;
    return out;
}
static bool IsInList(uint32_t value, uint32_t *list, size_t len) {
    for (int i = 0; i < len; i++) {
        if (value == list[i]) {
            return true;
        }
    }
    return false;
}

static Storage_Info *GetOrAddStorage(Graph_Info *gi, void *p, size_t sz, bool copy_data)
{
    for (int i = 0; i < gi->numStorages; i++) {
        Storage_Info *s = gi->storages[i];
        if (p == s->buffer && sz == s->size) {
            return s;
        }
    }

    // Create new storage.
    gi->numStorages++;
    gi->storages = realloc(gi->storages, gi->numStorages * sizeof(Storage_Info*));
    Storage_Info *newS = malloc(sizeof(Storage_Info));
    gi->storages[gi->numStorages - 1] = newS;
    newS->buffer = p;
    newS->size = sz;

    if (copy_data) {
        newS->static_data = malloc(sz);
        memcpy(newS->static_data, p, sz);
    } else {
        newS->static_data = NULL;
    }

    return newS;
}

Graph_Info *extract_graph_info(void *grt, const char *params_data, uint64_t params_size)
{
    TVMGraphRuntime *g = grt;

    assert(g->nodes_count == g->op_execs_count);

    TVMByteArray params;
    params.data = params_data;
    params.size = params_size;
    TVMGraphRuntime_LoadParams(g, params.data, params.size);

    size_t numStaticInputEIDs;
    uint32_t *staticInputEIDs = GetStaticInputEIDs(&numStaticInputEIDs, g, params.data, params.size);

    Graph_Info *gi = malloc(sizeof(Graph_Info));

    // These will be added dynamically.
    gi->numStorages = 0;
    gi->storages = NULL;
    gi->numInputs = 0;
    gi->inputs = NULL;
    gi->numOutputs = 0;
    gi->outputs = NULL;

    gi->numOps = g->nodes_count;
    gi->ops = malloc(g->nodes_count * sizeof(Op_Info));
    for (int i = 0; i < g->nodes_count; i++)
    {
        // See: TVMGraphRuntime_Run
        if (g->op_execs[i].fexec) {
            printf("op[%i]: %s\n", i, g->nodes[i].param.func_name);

            gi->ops[i].active = 1;
            strcpy(gi->ops[i].name, g->nodes[i].param.func_name);

            int numArgs = g->nodes[i].inputs_count + g->nodes[i].param.num_outputs;
            printf("  num args: %i\n", numArgs);
            gi->ops[i].numArgs = numArgs;
            gi->ops[i].args = malloc(numArgs * sizeof(Arg_Info));
            uint32_t *eids = malloc(numArgs * sizeof(uint32_t));
            for (int j = 0; j < g->nodes[i].inputs_count; j++) {
                eids[j] = TVMGraphRuntime_GetEntryId(g, g->nodes[i].inputs[j].node_id, g->nodes[i].inputs[j].index);
            }
            for (int j = 0; j < g->nodes[i].param.num_outputs; j++) {
                eids[j + g->nodes[i].inputs_count] = TVMGraphRuntime_GetEntryId(g, i, j);
            }
            for (int j = 0; j < numArgs; j++) {
                Arg_Info *arg = &gi->ops[i].args[j];
                arg->data = g->data_entry[eids[j]].dl_tensor.data;
                arg->offset = 0;
                arg->dataSize = GetTensorSize(&g->data_entry[eids[j]].dl_tensor);

                printf("    sz arg: %li  [%p]\n", arg->dataSize, arg->data);

                Storage_Info *storage = NULL;
                uintptr_t p = (uintptr_t)arg->data;
                for (int k = 0; k < g->storage_pool_count; k++) {
                    uintptr_t ps = (uintptr_t)g->storage_pool[k].array.dl_tensor.data;
                    size_t sz = GetTensorSize(&g->storage_pool[k].array.dl_tensor);
                    if (p >= ps && p + arg->dataSize <= ps + sz) {
                        // Arg is mapped to storage. Is static if part of params file.
                        storage = GetOrAddStorage(gi, (void*)ps, sz, IsInList(eids[j], staticInputEIDs, numStaticInputEIDs));
                        arg->offset = (uintptr_t)storage->buffer - (uintptr_t)arg->data;
                        break;
                    }
                }
                if (!storage) {
                    // Has to be static data.
                    storage = GetOrAddStorage(gi, arg->data, arg->dataSize, true);
                }
                arg->storage = storage;

                for (int k = 0; k < g->input_nodes_count; k++) {
                    if (IsInList(eids[j], staticInputEIDs, numStaticInputEIDs)) {
                        // Do not consider statically assigned args as input.
                        continue;
                    }
                    if (eids[j] == TVMGraphRuntime_GetEntryId(g, g->input_nodes[k], 0)) {
                        gi->numInputs++;
                        gi->inputs = realloc(gi->inputs, gi->numInputs * sizeof(Arg_Info*));
                        gi->inputs[gi->numInputs - 1] = arg;
                    }
                }
                for (int k = 0; k < g->outputs_count; k++) {
                    if (eids[j] == TVMGraphRuntime_GetEntryId(g, g->outputs[k].node_id, g->outputs[k].index)) {
                        gi->numOutputs++;
                        gi->outputs = realloc(gi->outputs, gi->numOutputs * sizeof(Arg_Info*));
                        gi->outputs[gi->numOutputs - 1] = arg;
                    }
                }
            }
            free(eids);
        } else {
            gi->ops[i].active = 0;
        }
    }

    free(staticInputEIDs);

    return gi;
}
