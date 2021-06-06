import string
import struct
from datetime import datetime


def fill(template, **kwargs):
    return string.Template(template).substitute(**kwargs)

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

def getSizes(tensors):
    out = "size_t sizes[] = { "
    for t in tensors:
        out += str(t.size) + ", "
    out += "};"
    return out


def generateTargetCode(outFileName, graph, params, modelInfo):
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

size_t TVMWrap_GetNumInputs()
{
    return ${numInputs};
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

size_t TVMWrap_GetNumOutputs()
{
    return ${numOutputs};
}
'''
        f.write(fill(
            mainCode,
            inMeta=getMeta(modelInfo.inTensors, True),
            outMeta=getMeta(modelInfo.outTensors),
            inNDims=2,
            outNDims=2,
            inSizes=getSizes(modelInfo.inTensors),
            outSizes=getSizes(modelInfo.outTensors),
            numInputs=len(modelInfo.inTensors),
            numOutputs=len(modelInfo.outTensors)))

