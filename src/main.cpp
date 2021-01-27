#include "CodeGen.h"

#include <fstream>
#include <sstream>


int main(int argc, char *argv[])
{
    if (argc < 4) {
        printf("Usage: %s graphFile paramFile outFile [workspaceSize]\n", argv[0]);
        return 1;
    }

    size_t workspaceSize = 0;
    if (argc >= 5) {
        workspaceSize = std::strtoul(argv[4], nullptr, 0);
    }

    std::ifstream graphFile(argv[1]);
    if (!graphFile) {
        printf("Could not open graph file\n");
        return 1;
    }
    std::stringstream ssGraphFile;
    ssGraphFile << graphFile.rdbuf();

    std::ifstream paramFile(argv[2], std::ios::binary | std::ios::ate);
    if (!paramFile) {
        printf("Could not open params file\n");
        return 1;
    }
    auto szParamFile = paramFile.tellg();
    paramFile.seekg(0, std::ios::beg);
    std::vector<char> paramData(szParamFile);
    if (!paramFile.read(paramData.data(), szParamFile)) {
        printf("Failed to read param file\n");
        return 1;
    }

    void *grt = create_tvm_rt(ssGraphFile.str().c_str(), paramData.data(), paramData.size());
    auto *gi = extract_graph_info(grt, paramData.data(), paramData.size());

    CodeGenerator cg(gi);
    cg.generateCode(argv[3], workspaceSize);

    return 0;
}
