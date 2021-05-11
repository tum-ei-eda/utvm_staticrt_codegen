import os
import sys
import logging
import shutil

import numpy as np

import tvm
import tvm.micro
from tvm import te
from tvm import relay
from tvm import ir
from tvm import autotvm
from tvm.contrib import graph_runtime

import tflite
from tflite.TensorType import TensorType as TType

import compiler_ext
import codegen

from tvm.relay.frontend.tflite import OperatorConverter
def get_custom_convert_map(model):
    from tvm.relay import op as _op
    import struct

    def convert_tflite_custom(self, op, builtin=False):
        """Convert TFLite custom op"""
        print("convert_tflite_custom")

        input_tensors = self.get_input_tensors(op)

        output_tensors = self.get_output_tensors(op)
        assert len(output_tensors) == 1, "output tensors length should be 1"
        output_tensor = output_tensors[0]
        output_tensor_shape = list(self.get_tensor_shape(output_tensor))
        output_tensor_type_str = self.get_tensor_type_str(output_tensor.tensor.Type())

        inputs = []
        for input_tensor in input_tensors:
            if self.has_expr(input_tensor.tensor_idx):
                inputs.append(self.get_expr(input_tensor.tensor_idx))
            else:
                input_value = self.get_tensor_value(input_tensor)
                input_tensor_type_str =  self.get_tensor_type_str(input_tensor.tensor.Type())
                inputs.append(self.exp_tab.new_const(input_value, dtype=input_tensor_type_str))
        #inputs = [ relay.annotation.compiler_begin(input_expr), "tflitecompiler") for input_expr in inputs]

        try:
            from tflite.TensorType import TensorType
        except ImportError:
            raise ImportError("The tflite package must be installed")

        op_code = model.OperatorCodes(op.OpcodeIndex())
        if builtin:
            from tflite.BuiltinOptions import BuiltinOptions
            from tflite.BuiltinOperator import BuiltinOperator
            op_options = op.BuiltinOptions()
            if op_code.BuiltinCode() == BuiltinOperator.FULLY_CONNECTED:
                from tflite.FullyConnectedOptions import FullyConnectedOptions
                fully_connected_options = FullyConnectedOptions()
                fully_connected_options.Init(op_options.Bytes, op_options.Pos)
                builtin_options_dict = {
                    'activation': fully_connected_options.FusedActivationFunction(),
                    'weights_format': fully_connected_options.WeightsFormat(),
                    'keep_num_dims': fully_connected_options.KeepNumDims(),
                    'asymmetric_quantize_inputs': fully_connected_options.AsymmetricQuantizeInputs()
                }
                builtin_options_raw = struct.pack("IIBB", *builtin_options_dict.values())
                out = _op.contrib.tflite_extern(inputs, name="FULLY_CONNECTED", builtin=True, options=list(builtin_options_raw), out_dtype=output_tensor_type_str, out_shape=output_tensor_shape)
            elif op_code.BuiltinCode() == BuiltinOperator.ADD:
                from tflite.AddOptions import AddOptions
                add_options = AddOptions()
                add_options.Init(op_options.Bytes, op_options.Pos)
                builtin_options_dict = {
                    'activation': add_options.FusedActivationFunction(),
                    'pot_scale_int16': add_options.PotScaleInt16()
                }
                builtin_options_raw = struct.pack("IB", *builtin_options_dict.values())
                out = _op.contrib.tflite_extern(inputs, name="ADD", builtin=True, options=list(builtin_options_raw), out_dtype=output_tensor_type_str, out_shape=output_tensor_shape)
            elif op_code.BuiltinCode() == BuiltinOperator.CONV_2D:
                from tflite.Conv2DOptions import Conv2DOptions
                conv_options = Conv2DOptions()
                conv_options.Init(op_options.Bytes, op_options.Pos)
                builtin_options_dict = {
                    'padding': conv_options.Padding(),
                    'stride_width': conv_options.StrideW(),
                    'stride_height': conv_options.StrideH(),
                    'activation': conv_options.FusedActivationFunction(),
                    'dilation_width_factor': conv_options.DilationWFactor(),
                    'dilation_height_factor': conv_options.DilationHFactor()
                }
                builtin_options_raw = struct.pack("IIIIII", *builtin_options_dict.values())
                out = _op.contrib.tflite_extern(inputs, name="CONV_2D", builtin=True, options=list(builtin_options_raw), out_dtype=output_tensor_type_str, out_shape=output_tensor_shape)
            else:
                raise NotImplementedError
        else:
            assert(op_code.BuiltinCode() == tflite.BuiltinOperator.CUSTOM)
            flexbuffer = op.CustomOptionsAsNumpy().tobytes()
            op_code_list_idx = op.OpcodeIndex()
            custom_op_code_str = self.model.OperatorCodes(op_code_list_idx).CustomCode().decode('utf-8')
            print("CUSTOM:", custom_op_code_str)
            out = _op.contrib.tflite_extern(inputs, name=custom_op_code_str, builtin=False, options=list(flexbuffer), out_dtype=output_tensor_type_str, out_shape=output_tensor_shape)

        #out = relay.annotation.compiler_end(out, "tflitecompiler")
        return out

    def convert_add_wrapper(self, op):
        print("ADD")

        replace_with_tflite_op = True
        if replace_with_tflite_op:
            return convert_tflite_custom(self, op, builtin=True)
        else:
            return self.convert_add(op)

    def convert_fully_connected_wrapper(self, op):
        print("FULLY_CONNECTED")
        replace_with_tflite_op = True
        if replace_with_tflite_op:
            return convert_tflite_custom(self, op, builtin=True)
        else:
            return self.convert_fully_connected(op)

    def convert_conv2d_wrapper(self, op):
        print("CONV_2D")

        def use_tflite(op):
            try:
                from tflite.BuiltinOptions import BuiltinOptions
                from tflite.TensorType import TensorType
                from tflite.Conv2DOptions import Conv2DOptions
                from tflite.DepthwiseConv2DOptions import DepthwiseConv2DOptions
                from tflite.Padding import Padding
            except ImportError:
                raise ImportError("The tflite package must be installed")
            input_tensors = self.get_input_tensors(op)
            output_tensors = self.get_output_tensors(op)

            input_tensor = input_tensors[0]
            weight_tensor = input_tensors[1]
            if len(input_tensors) == 3:
                bias_tensor = input_tensors[2]
            else:
                bias_tensor = None
            output_tensor = output_tensors[0]

            input_tensor_type = input_tensor.tensor.Type()
            weight_tensor_type = weight_tensor.tensor.Type()
            output_tensor_type = output_tensor.tensor.Type()
            if bias_tensor is not None:
                bias_tensor_type = bias_tensor.tensor.Type()

            op_options = op.BuiltinOptions()
            conv_options = Conv2DOptions()
            conv_options.Init(op_options.Bytes, op_options.Pos)

            stride_h = conv_options.StrideH()
            stride_w = conv_options.StrideW()

            dilation_h = conv_options.DilationHFactor()
            dilation_w = conv_options.DilationWFactor()

            padding = conv_options.Padding()

            fused_activation_fn = conv_options.FusedActivationFunction()

            _, input_h, input_w, input_c = to_int_list(self.get_tensor_shape(input_tensor))
            output_channels, kernel_h, kernel_w, _ = to_int_list(
                self.get_tensor_shape(weight_tensor)
            )

            dilated_kernel_h = dilation_h * (kernel_h - 1) + 1
            dilated_kernel_w = dilation_w * (kernel_w - 1) + 1

            if input_tensor.qnn_params:
                pass
            if output_tensor.qnn_params:
                pass

            # Final decision
            print("types: ", output_tensor_type, bias_tensor_type, weight_tensor_type, TensorType.FLOAT32)

            if output_tensor_type == TensorType.FLOAT32 and weight_tensor_type == TensorType.FLOAT32 and bias_tensor_type == TensorType.FLOAT32:
                return True
            else:
                return False

        replace_with_tflite_op = True
        if replace_with_tflite_op:
            return convert_tflite_custom(self, op, builtin=True)
        else:
            return self.convert_conv2d(op)
    return {
        "ADD": convert_add_wrapper,
        "FULLY_CONNECTED": convert_fully_connected_wrapper,
        "CONV_2D": convert_conv2d_wrapper,
        "CUSTOM": convert_tflite_custom,
    }

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
    def __init__(self):
        self.opt_level = 3
        self.local = False
        if self.local:
            self.target = "llvm"
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

        custom_convert_map = get_custom_convert_map(tflModel)

        self.mod, self.params = relay.frontend.from_tflite(tflModel, shape_dict=shapes, dtype_dict=types, custom_convert_map=custom_convert_map)
        self.mod = tvm.relay.transform.PartitionGraph()(self.mod)


    def build(self):
        print("### TVMFlow.build")

        if self.local:
            cfg = {}
        else:
            cfg = { "tir.disable_vectorize": True }

        with tvm.transform.PassContext(opt_level=self.opt_level, config=cfg):
            c_mod = relay.build(self.mod, target=self.target, params=self.params)
            self.graph = c_mod.get_graph_json()
            self.c_params = c_mod.get_params()

        if not self.local:
            # Cross compile
            self.workspace = tvm.micro.Workspace(debug=True)
            opts = tvm.micro.default_options(os.path.join(tvm.micro.get_standalone_crt_dir(), "template", "host"))
            self.compiler = compiler_ext.Compiler_Ext(target=self.target)
            self.micro_binary = tvm.micro.build_static_runtime(
                self.workspace,
                self.compiler,
                c_mod,
                opts,
                extra_libs=[tvm.micro.get_standalone_crt_lib("memory")]
            )

            # Prepare target data
            outDir = "out"
            os.makedirs(outDir, exist_ok=True)
            shutil.copy2(self.workspace.path + "/src/module/lib1.c", outDir + "/kernels.c")
            shutil.copy2(self.workspace.path + "/src/module/lib0.c", outDir + "/syslib.c")
            try_index = 2;
            while os.path.isfile(self.workspace.path + f"/src/module/lib{try_index}.c"):
                shutil.copy2(self.workspace.path + f"/src/module/lib{try_index}.c", outDir + f"/kernels{try_index}.c")
                try_index = try_index + 1
            with open(outDir + "/graph.json", "w") as f:
                f.write(self.graph)
            with open(outDir + "/params.bin", "wb") as f:
                f.write(relay.save_param_dict(self.c_params))
            codegen.generateTargetCode(outDir + "/runtime_wrapper.c", self.graph, relay.save_param_dict(self.c_params), self.modelInfo)


def main():
    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "model.tflite")
        sys.exit(1)

    flow = TVMFlow()
    flow.loadModel(sys.argv[1])
    flow.build()

if __name__ == "__main__":
    main()
