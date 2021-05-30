PROJECT(graph_runtime)

SET(GRAPH_SRC
    ${OUT_DIR}/runtime_wrapper.c
)

IF(EXISTS ${GRAPH_SRC})
    ADD_EXECUTABLE(${PROJECT_NAME}
        ${COMMON_SRCS}
        ${GRAPH_SRC}
    )

    TARGET_INCLUDE_DIRECTORIES(${PROJECT_NAME} PUBLIC
        ${PROJECT_SOURCE_DIR}/..
    )

    TARGET_LINK_LIBRARIES(${PROJECT_NAME} tvm_graph_rt)
ELSE()
    MESSAGE(STATUS "Skipping aot_runtime because ${GRAPH_SRC} was not generated...")
ENDIF()
