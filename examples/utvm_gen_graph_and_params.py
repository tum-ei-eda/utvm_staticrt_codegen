import os
import sys
import logging
import shutil
import argparse
import tarfile
import json

import numpy as np

import tvm
import tvm.micro
from tvm import te
from tvm import relay
from tvm import ir
from tvm import autotvm
from tvm.contrib import graph_runtime
from tvm.contrib import utils as tvm_utils
from tvm.micro import export_model_library_format

from tflite.TensorType import TensorType as TType

import compiler_ext
import codegen


class TensorInfo:
    def __init__(self, t):
        self.name = t.Name().decode()

        typeLookup = {
            TType.FLOAT32: (4, "float32"),
            TType.UINT8: (1, "uint8"),
            TType.INT8: (1, "int8")
        }
        self.tysz, self.ty = typeLookup[t.Type()]
        assert self.ty != ""

        shape = tuple([t.Shape(si) for si in range(0, t.ShapeLength())])
        self.shape = shape

        self.size = self.tysz
        for dimSz in self.shape:
            self.size *= dimSz


class ModelInfo:
    def __init__(self, model):
        assert model.SubgraphsLength() == 1
        g = model.Subgraphs(0)

        self.inTensors = []
        for i in range(0, g.InputsLength()):
            t = g.Tensors(g.Inputs(i))
            self.inTensors.append(TensorInfo(t))

        self.outTensors = []
        for i in range(0, g.OutputsLength()):
            t = g.Tensors(g.Outputs(i))
            self.outTensors.append(TensorInfo(t))


class TVMFlow:
    def __init__(self, aot=False, outDir=os.path.join(os.getcwd(), "out")):
        self.opt_level = 3
        self.local = False
        self.useAOT = aot
        self.outDir = outDir
        if self.local:
            self.target = "llvm"
        else:
            if self.useAOT:
                self.target = tvm.target.Target("c -runtime=c --link-params --executor=aot --workspace-byte-alignment=1")
            else:
                self.target = tvm.target.target.micro("host")


    def loadModel(self, path):
        print("### TVMFlow.loadModel")

        modelBuf = open(path, "rb").read()

        import tflite
        tflModel = tflite.Model.GetRootAsModel(modelBuf, 0)

        shapes = {}
        types = {}

        self.modelInfo = ModelInfo(tflModel)
        for t in self.modelInfo.inTensors:
            print("Input", '"' + t.name + '"', t.ty, t.shape)
            shapes[t.name] = t.shape
            types[t.name] = t.ty

        self.mod, self.params = relay.frontend.from_tflite(tflModel, shape_dict=shapes, dtype_dict=types)


    def build(self):
        print("### TVMFlow.build")

        if self.local:
            cfg = {}
        else:
            cfg = { "tir.disable_vectorize": True }

        with tvm.transform.PassContext(opt_level=self.opt_level, config=cfg):
            c_mod = relay.build(self.mod, target=self.target, params=self.params)
            if not self.useAOT:
                self.graph = c_mod.get_graph_json()
            else:
                self.graph = None
            self.c_params = c_mod.get_params()

        if not self.local:
            # Extract metadata.
            mlfDir = tvm_utils.tempdir().temp_dir
            os.makedirs(mlfDir, exist_ok=True)
            tarFile = os.path.join(mlfDir, "archive.tar")
            export_model_library_format(c_mod, tarFile)
            tarfile.open(tarFile).extractall(mlfDir)

            # Cross compile
            if not self.useAOT:
                self.workspace = tvm.micro.Workspace(debug=True)
                opts = tvm.micro.default_options(os.path.join(tvm.micro.get_standalone_crt_dir(), "template", "host"))
                self.compiler = compiler_ext.Compiler_Ext(target=self.target)
                self.micro_binary = tvm.micro.build_static_runtime(
                    self.workspace,
                    self.compiler,
                    c_mod,
                    opts,
                    executor="aot" if self.useAOT else "host-driven",
                    extra_libs=[tvm.micro.get_standalone_crt_lib("memory")]
                )

            if os.path.exists(os.path.join(self.outDir, "params.bin")):
                shutil.rmtree(self.outDir)

            shutil.copytree(os.path.join(mlfDir, "codegen", "host", "src"), self.outDir)
            shutil.copy2(os.path.join(mlfDir, "relay.txt"), os.path.join(self.outDir, "relay.txt"))
            shutil.copy2(os.path.join(mlfDir, "metadata.json"), os.path.join(self.outDir, "metadata.json"))

            if self.graph:
                with open(os.path.join(self.outDir, "graph.json"), "w") as f:
                    f.write(self.graph)

            with open(os.path.join(self.outDir, "metadata.json")) as json_f:
                metadata = json.load(json_f)
            workspaceBytes = 0
            for op in metadata["memory"]["functions"]["operator_functions"]:
                workspaceBytes = max(workspaceBytes, op["workspace"][0]["workspace_size_bytes"])
            with open(os.path.join(self.outDir, "workspace_size.txt"), "w") as f:
                f.write(str(workspaceBytes))

            with open(os.path.join(self.outDir, "params.bin"), "wb") as f:
                f.write(relay.save_param_dict(self.c_params))

            if self.useAOT:
                workspaceBytes = metadata["memory"]["functions"]["main"][0]["workspace_size_bytes"]
                codegen.generateTargetCodeAOT(os.path.join(self.outDir, "aot_wrapper.c"), self.modelInfo, workspace=workspaceBytes)
            else:
                codegen.generateTargetCodeRT(os.path.join(self.outDir, "runtime_wrapper.c"), self.graph, relay.save_param_dict(self.c_params), self.modelInfo)



def main():
    parser = argparse.ArgumentParser(description='Run TVM Flow')
    parser.add_argument('model', metavar="MODEL", type=str, nargs=1, help='Model to process')
    parser.add_argument('--aot', action='store_true',
                        help='Use AOT FLow (default: %(default)s)')
    parser.add_argument('--out-dir', '-o', dest='outdir', metavar='DIR', type=str,
                        default=os.path.join(os.getcwd(), 'out'), help='''Output directory
(default: %(default)s)''')

    args = parser.parse_args()

    flow = TVMFlow(aot=args.aot, outDir=args.outdir)
    flow.loadModel(sys.argv[1])
    flow.build()

if __name__ == "__main__":
    main()
