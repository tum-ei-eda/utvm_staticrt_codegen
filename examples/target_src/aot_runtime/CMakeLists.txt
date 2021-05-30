PROJECT(aot_runtime)

SET(AOT_SRC
    ${OUT_DIR}/aot_wrapper.c
)

IF(EXISTS ${AOT_SRC})
    ADD_EXECUTABLE(${PROJECT_NAME}
        ${COMMON_SRCS}
        ${AOT_SRC}
    )

    TARGET_INCLUDE_DIRECTORIES(${PROJECT_NAME} PUBLIC
        ${PROJECT_SOURCE_DIR}/..
    )

    TARGET_LINK_LIBRARIES(${PROJECT_NAME} tvm_aot_rt)
ELSE()
    MESSAGE(STATUS "Skipping aot_runtime because ${AOT_SRC} was not generated...")
ENDIF()

