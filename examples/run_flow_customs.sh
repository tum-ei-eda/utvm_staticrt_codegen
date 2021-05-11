#!/bin/bash

set -e

run_test() {
    python3 utvm_gen_graph_and_params.py data/$1
    ../build/utvm_staticrt_codegen out/graph.json out/params.bin out/staticrt.c $2

    cd target_src
    mkdir -p build
    cd build
    cmake -DCMAKE_BUILD_TYPE=DEBUG -DTFLITE_FALLBACK=ON ..

    # Static Runtime
    make static_runtime
    ./static_runtime/static_runtime

    # Graph Runtime
    make graph_runtime
    ./graph_runtime/graph_runtime

    cd ../..
}

#run_test sine_model.tflite 0
#run_test model_with_add.tflite 0
#run_test model_with_add2.tflite 0
#run_test sine_model.tflite 0
run_test cifar10.tflite 28800
