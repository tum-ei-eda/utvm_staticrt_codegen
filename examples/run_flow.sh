#!/bin/bash

set -e

run_test() {
    TARGET=$1
    MODEL=data/$2

    if [[ "$TARGET" == "aot_runtime" ]]
    then
        python3 utvm_gen_graph_and_params.py $MODEL --aot
    else
        python3 utvm_gen_graph_and_params.py $MODEL
        ../build/utvm_staticrt_codegen out/graph.json out/params.bin out/staticrt.c $(cat out/workspace_size.txt)
    fi

    TVM_DIR=$(grep TVM_DIR ../build/CMakeCache.txt)

    mkdir -p target_src/build
    cd target_src/build
    cmake -D$TVM_DIR -DCMAKE_BUILD_TYPE=Debug ..

    make $TARGET
    ./$TARGET/$TARGET

    cd -
}

run_tests() {
    run_test static_runtime $1
    run_test graph_runtime $1
    run_test aot_runtime $1
}

run_tests sine_model.tflite
run_tests cifar10.tflite
