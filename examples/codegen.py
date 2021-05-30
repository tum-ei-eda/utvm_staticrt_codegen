import string
import struct
from datetime import datetime


def fill(template, **kwargs):
    return string.Template(template).substitute(**kwargs)


def getSizes(tensors):
    out = "size_t sizes[] = { "
    for t in tensors:
        out += str(t.size) + ", "
    out += "};"
    return out


def generateTargetCodeRT(outFileName, graph, params, modelInfo):

    def escapeJson(j):
        return j.replace("\"", "\\\"").replace("\n", "\\\n")

    def toCArray(bin):
        result = ""
        for c in bin:
            result += hex(c) + ", "
        return result

    def getMeta(tensors, withNames=False):
        out = ""
        if withNames:
            out = "const char *names[] = { "
            for t in tensors:
                out += "\"" + t.name + "\", "
            out += "};\n    "

        out += "DLDataType dtypes[] = {"
        for t in tensors:
            if t.ty == "float32":
                out += "{kDLFloat, 32, 1}"
            elif t.ty == "uint8":
                out += "{kDLUInt, 8, 1}"
            elif t.ty == "int8":
                out += "{kDLInt, 8, 1}"
            else:
                raise "Invalid type"
            out += ", "
        out += "};\n    "

        for i, t in enumerate(tensors):
            out += "int64_t shape_" + str(i) + "[] = { "
            for s in t.shape:
                out += str(s) + ", "
            out += "};\n    "
        out += "int64_t *shapes[] = { "
        for i, t in enumerate(tensors):
            out += "shape_" + str(i) + ", "
        out += "};\n"

        for i, t in enumerate(tensors):
            out += "    static uint8_t data_" + str(i) + "[" + str(t.size) + "];\n"
        out += "    uint8_t *data[] = { "
        for i, t in enumerate(tensors):
            out += "data_" + str(i) + ", "
        out += "};"

        return out

    with open(outFileName, "w") as f:
        header = '''// This file is generated. Do not edit.
// Generated on: ${time}

#include <stdint.h>
#include "tvm/runtime/c_runtime_api.h"
#include "tvm/runtime/crt/packed_func.h"
#include "bundle.h"

'''
        f.write(fill(header, time=datetime.now()))

        f.write("const char * const g_graph = \"" + escapeJson(graph) + "\";\n")
        f.write("const unsigned char g_params[] = { " + toCArray(params) + "\n};\n")
        f.write("const uint64_t g_params_size = " + str(len(params)) + ";\n")

        mainCode = '''

TVMModuleHandle TVMArgs_AsModuleHandle(const TVMArgs* args, size_t index);

void *g_handle = NULL;

void TVMWrap_Init()
{
    g_handle = tvm_runtime_create(g_graph, g_params, g_params_size, NULL);
}

void *TVMWrap_GetInputPtr(int index)
{
    ${inMeta}

    DLTensor input;
    input.data = (void*)data[index];
    DLDevice device = {kDLCPU, 0};
    input.device = device;
    input.ndim = ${inNDims};
    input.dtype = dtypes[index];
    input.shape = shapes[index];
    input.strides = NULL;
    input.byte_offset = 0;

    tvm_runtime_set_input(g_handle, names[index], &input);

    return data[index];
}

size_t TVMWrap_GetInputSize(int index)
{
    ${inSizes}

    return sizes[index];
}

void TVMWrap_Run()
{
    tvm_runtime_run(g_handle);
}

void *TVMWrap_GetOutputPtr(int index)
{
    ${outMeta}

    DLTensor output;
    output.data = (void*)data[index];
    DLDevice device = {kDLCPU, 0};
    output.device = device;
    output.ndim = ${outNDims};
    output.dtype = dtypes[index];
    output.shape = shapes[index];
    output.strides = NULL;
    output.byte_offset = 0;

    tvm_runtime_get_output(g_handle, index, &output);

    return data[index];
}

size_t TVMWrap_GetOutputSize(int index)
{
    ${outSizes}

    return sizes[index];
}
'''
        f.write(fill(
            mainCode,
            inMeta=getMeta(modelInfo.inTensors, True),
            outMeta=getMeta(modelInfo.outTensors),
            inNDims=2,
            outNDims=2,
            inSizes=getSizes(modelInfo.inTensors),
            outSizes=getSizes(modelInfo.outTensors)))


def generateTargetCodeAOT(outFileName, modelInfo, workspace=None):

    def writeTensors(tensors, prefix):
        lenTensors = len(tensors)
        out = ""
        tensorNames = [ prefix + str(i) + "_data" for i in range(lenTensors)]
        for i, t in enumerate(tensors):
            out += "char " + tensorNames[i] + "[" + str(t.size) + "];\n"
        out += "void* " + prefix + "s[] = {" + ", ".join(tensorNames) +"};\n"
        return out

    with open(outFileName, "w") as f:
        header = '''// This file is generated. Do not edit.
// Generated on: ${time}

// TODO: Get rid of unused includes!
#include <stdlib.h>
#include <stdarg.h>
#include <stdio.h>
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <dlpack/dlpack.h>
#include "tvm/runtime/crt/internal/aot_executor/aot_executor.h"
#include "tvm/runtime/crt/stack_allocator.h"
#include "printing.h"

'''
        f.write(fill(header, time=datetime.now()))

        tensors_code = '''
${inTensors}
${outTensors}
'''

        f.write(fill(tensors_code, inTensors=writeTensors(modelInfo.inTensors, "input"), outTensors=writeTensors(modelInfo.outTensors, "output")))

        if workspace is None:
            workspaceInit = ""
        else:
            workspaceInit = "    StackMemoryManager_Init(&app_workspace, g_aot_memory, WORKSPACE_SIZE);"
            workspace_code = '''
#define WORKSPACE_SIZE (${workspaceBytes})
static uint8_t g_aot_memory[WORKSPACE_SIZE];
tvm_workspace_t app_workspace;

tvm_crt_error_t TVMPlatformMemoryAllocate(size_t num_bytes, DLDevice dev, void** out_ptr) {
    DBGPRINTF("Allocating %d bytes... (%d bytes left)\\n", num_bytes, app_workspace.workspace+app_workspace.workspace_size-app_workspace.next_alloc);
    return StackMemoryManager_Allocate(&app_workspace, num_bytes, out_ptr);
}
tvm_crt_error_t TVMPlatformMemoryFree(void* ptr, DLDevice dev) {
    DBGPRINTF("Freeing %d bytes...\\n", app_workspace.next_alloc-(uint8_t*)ptr);
    return StackMemoryManager_Free(&app_workspace, ptr);
}
'''
            f.write(fill(workspace_code, workspaceBytes=workspace))

        mainCode = '''
void TVMPlatformAbort(tvm_crt_error_t code) { exit(1); }

void TVMLogf(const char* msg, ...) {
  va_list args;
  va_start(args, msg);
  DBGPRINTF(msg, args);
  va_end(args);
}

TVM_DLL int TVMFuncRegisterGlobal(const char* name, TVMFunctionHandle f, int override) { }

extern tvm_model_t network;


void TVMWrap_Init()
{
''' + workspaceInit + '''
}

void *TVMWrap_GetInputPtr(int index)
{
    return inputs[index];
}

size_t TVMWrap_GetInputSize(int index)
{
    ${inSizes}

    return sizes[index];
}

void TVMWrap_Run()
{
    tvm_runtime_run(&network, inputs, outputs);
}

void *TVMWrap_GetOutputPtr(int index)
{
    return outputs[index];
}

size_t TVMWrap_GetOutputSize(int index)
{
    ${outSizes}

    return sizes[index];
}
'''
        f.write(fill(
            mainCode,
            inSizes=getSizes(modelInfo.inTensors),
            outSizes=getSizes(modelInfo.outTensors)))
