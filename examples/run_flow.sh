#!/bin/bash

set -e

run_test() {
    python3 utvm_gen_graph_and_params.py data/$1
    ../build/utvm_staticrt_codegen out/graph.json out/params.bin out/staticrt.c $2

    cd target_src
    mkdir -p build
    cd build
    cmake -DCMAKE_BUILD_TYPE=Debug ..
    make

    ./example_target_src

    cd ../..
}

run_test sine_model.tflite 0
run_test cifar10.tflite 28800
