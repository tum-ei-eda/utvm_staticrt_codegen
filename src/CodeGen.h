#ifndef UTVMSTATICRTCODEGEN_CODEGEN_H
#define UTVMSTATICRTCODEGEN_CODEGEN_H

#include "TVMInfoExtraction.h"

#include <vector>
#include <string>
#include <memory>


class CodeGenerator
{
public:
    CodeGenerator(const Graph_Info *gi);

    void generateCode(const std::string &outFileName, size_t workspaceSize);

private:
    struct Storage {
        size_t sz;
        std::vector<uint8_t> staticData;
    };
    std::vector<Storage> m_storages;

    struct Arg {
        int storageIndex;
        ptrdiff_t offset;
        size_t sz;
    };
    struct Op {
        std::string name;
        std::vector<std::unique_ptr<Arg>> args;
    };
    std::vector<Op> m_ops;
    std::vector<Arg *> m_inArgs;
    std::vector<Arg *> m_outArgs;
};

#endif
