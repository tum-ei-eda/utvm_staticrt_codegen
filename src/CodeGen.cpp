#include "CodeGen.h"

#include <sstream>
#include <fstream>
#include <iomanip>
#include <map>
#include <ctime>
#include <algorithm>


static std::string GetByteArrayCode(const void *data, size_t len) {
    std::stringstream out;
    out << "{\"";
    for (size_t i = 0; i < len; i++) {
        out << "\\x" << std::setw(2) << std::setfill('0') << std::hex
            << (int)((unsigned char *)data)[i];
    }
    out << "\"}";
    return out.str();
}


CodeGenerator::CodeGenerator(const Graph_Info *gi)
{
    std::map<Storage_Info *, int> storageToNewStorageIndex;
    for (int i = 0; i < gi->numStorages; i++) {
        Storage_Info *s = gi->storages[i];
        std::vector<uint8_t> data;
        if (s->static_data) {
            data.assign(s->static_data, s->static_data + s->size);
        }
        m_storages.push_back({ s->size, std::move(data) });
        storageToNewStorageIndex[s] = m_storages.size() - 1;
    }

    std::map<Arg_Info *, Arg *> argToNewArg;
    for (int i = 0; i < gi->numOps; i++) {
        auto &op = gi->ops[i];
        if (op.active) {
            std::vector<std::unique_ptr<Arg>> args;
            for (int j = 0; j < op.numArgs; j++) {
                auto &arg = op.args[j];
                int index = storageToNewStorageIndex[arg.storage];
                std::unique_ptr<Arg> newArg(new Arg{ index, arg.offset, arg.dataSize });
                argToNewArg[&op.args[j]] = newArg.get();
                args.push_back(std::move(newArg));
            }
            m_ops.push_back({ op.name, std::move(args) });
        }
    }

    for (int i = 0; i < gi->numInputs; i++) {
        m_inArgs.push_back(argToNewArg[gi->inputs[i]]);
    }
    for (int i = 0; i < gi->numOutputs; i++) {
        m_outArgs.push_back(argToNewArg[gi->outputs[i]]);
    }
}

void CodeGenerator::generateCode(const std::string &outFileName, size_t workspaceSize)
{
    std::ofstream out(outFileName);

    out << "// This file is generated. Do not edit.\n";
    {
        auto t = std::time(nullptr);
        auto tm = *std::localtime(&t);
        out << "// Generated on: " << std::put_time(&tm, "%d.%m.%Y %H:%M:%S")
            << "\n";
    }

    out << "#include <stdlib.h>\n";
    out << "#include <string.h>\n";
    out << "#include <tvm/runtime/crt/error_codes.h>\n";
    out << "#include \"tvm/runtime/c_runtime_api.h\"\n\n";
    out << "#include \"tvm/runtime/crt/stack_allocator.h\"\n\n";

    out << "typedef struct ArgInfo { void *buffer; size_t size; } ArgInfo;\n\n";

    out << "tvm_workspace_t g_workspace;\n";
    out << "#define WORKSPACE_SIZE (" << workspaceSize << ")\n";
    out << "static uint8_t g_workspace_buf[WORKSPACE_SIZE];\n";

    // Generate RAM buffers.
    for (size_t i = 0; i < m_storages.size(); i++) {
        auto &s = m_storages[i];
        out << "static " << (s.staticData.empty() ? "" : "const ") << "uint8_t g_storage_" << i << "[" << s.sz << "]";
        if (!s.staticData.empty()) {
            out << " = " << GetByteArrayCode(s.staticData.data(), s.staticData.size());
        }
        out << ";\n";
    }
    out << "\n";

    // Declare kernel funcs that were generated by tvm.
    // Omit unused parameters, because the RISC-V ABI allows it.
    out << "void __nop(void *x, void *y) {}\n";
    for (auto &op : m_ops) {
        out << "void " << op.name << "(void *, void*);\n";
    }

    out << "\nvoid TVMWrap_Run() {\n";

    for (size_t i = 0; i < m_ops.size(); i++) {
        auto &op = m_ops[i];

        out << "  TVMValue args_" << i << "[" << op.args.size() << "];\n";
        out << "  int32_t arg_type_ids_" << i << "[" << op.args.size() << "];\n";

        for (size_t j = 0; j < op.args.size(); j++) {
            std::string argName = "arg_" + std::to_string(i) + "_" + std::to_string(j);
            out << "  DLTensor " << argName << ";\n";
            out << "  " << argName << ".data = (void*)&g_storage_" << op.args[j]->storageIndex << "[" << op.args[j]->offset << "];\n";
            out << "  args_" << i << "[" << j << "].v_handle = &" << argName << ";\n";
        }

        out << "  " << op.name << "(args_" << i << ", arg_type_ids_" << i << ");\n\n";
    }

    out << "}\n";

    out << "\nvoid TVMWrap_Init()\n{\n";
    if (workspaceSize) {
        out << "  StackMemoryManager_Init(&g_workspace, g_workspace_buf, WORKSPACE_SIZE);\n";
    }
    out << "}\n";
    out << "static const ArgInfo inArgInfo[] = {";
    for (auto &arg : m_inArgs) {
        out << "{&g_storage_" << arg->storageIndex << "[" << arg->offset << "]," << arg->sz << "}, ";
    }
    out << "};\nstatic const ArgInfo outArgInfo[] = {";
    for (auto &arg : m_outArgs) {
        out << "{&g_storage_" << arg->storageIndex << "[" << arg->offset << "]," << arg->sz << "}, ";
    }
    out << R"CODE(};
void *TVMWrap_GetInputPtr(int index)
{
  return inArgInfo[index].buffer;
}
size_t TVMWrap_GetInputSize(int index)
{
  return inArgInfo[index].size;
}
size_t TVMWrap_GetNumInputs()
{
  return )CODE" << m_inArgs.size() << R"CODE(;
}
void *TVMWrap_GetOutputPtr(int index)
{
  return outArgInfo[index].buffer;
}
size_t TVMWrap_GetOutputSize(int index)
{
  return outArgInfo[index].size;
}
size_t TVMWrap_GetNumOutputs()
{
  return )CODE" << m_outArgs.size() << R"CODE(;
}

void* TVMBackendAllocWorkspace(int device_type, int device_id, uint64_t nbytes, int dtype_code_hint,
                               int dtype_bits_hint) {
  void *out_ptr = NULL;
  tvm_crt_error_t err = StackMemoryManager_Allocate(&g_workspace, nbytes, &out_ptr);
  return out_ptr;
}

int TVMBackendFreeWorkspace(int device_type, int device_id, void* ptr) {
  return StackMemoryManager_Free(&g_workspace, ptr);
}

void TVMPlatformAbort(tvm_crt_error_t code) {
  exit(1);
}
)CODE";

}
