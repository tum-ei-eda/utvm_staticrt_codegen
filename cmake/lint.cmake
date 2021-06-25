INCLUDE(ExternalProject)
FIND_PACKAGE(Git REQUIRED)

SET(CHECK_FILES
    #${PROJECT_SOURCE_DIR}/src/*.c
    #${PROJECT_SOURCE_DIR}/src/*.cc
    ${PROJECT_SOURCE_DIR}/src/*.cpp
    ${PROJECT_SOURCE_DIR}/src/*.h
    ${PROJECT_SOURCE_DIR}/examples/target_src/*.c
    #${PROJECT_SOURCE_DIR}/examples/target_src/*.cc
    ${PROJECT_SOURCE_DIR}/examples/target_src/*.h
    )

SET(TIDY_SOURCES
    ${PROJECT_SOURCE_DIR}/src/
    ${PROJECT_SOURCE_DIR}/examples/target_src/
    )

# ------------------------------------------------------------------------------
# All checks
# ------------------------------------------------------------------------------

IF(ALL_CHECKS)
    SET(ENABLE_ASTYLE ON)
    SET(ENABLE_CLANG_TIDY ON)
    SET(ENABLE_CPPCHECK ON)
ENDIF()

# ------------------------------------------------------------------------------
# Git whitespace
# ------------------------------------------------------------------------------


ADD_CUSTOM_TARGET(
    commit
    COMMAND echo COMMAND ${GIT_EXECUTABLE} diff --check HEAD^
    COMMENT "Running git check"
)

# ------------------------------------------------------------------------------
# Astyle
# ------------------------------------------------------------------------------

IF(ENABLE_ASTYLE)

    LIST(APPEND ASTYLE_CMAKE_ARGS
        "-DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}"
    )

    EXTERNALPROJECT_ADD(
        astyle
        GIT_REPOSITORY      https://github.com/Bareflank/astyle.git
        GIT_TAG             v1.2
        GIT_SHALLOW         1
        CMAKE_ARGS          ${ASTYLE_CMAKE_ARGS}
        PREFIX              ${CMAKE_BINARY_DIR}/external/astyle/prefix
        TMP_DIR             ${CMAKE_BINARY_DIR}/external/astyle/tmp
        STAMP_DIR           ${CMAKE_BINARY_DIR}/external/astyle/stamp
        DOWNLOAD_DIR        ${CMAKE_BINARY_DIR}/external/astyle/download
        SOURCE_DIR          ${CMAKE_BINARY_DIR}/external/astyle/src
        BINARY_DIR          ${CMAKE_BINARY_DIR}/external/astyle/build
    )

    LIST(APPEND ASTYLE_ARGS
        --style=linux
        --lineend=linux
        --suffix=none
        --pad-oper
        --unpad-paren
        --break-closing-brackets
        --align-pointer=name
        --align-reference=name
        --indent-preproc-define
        --indent-switches
        --indent-col1-comments
        --keep-one-line-statements
        --keep-one-line-blocks
        --pad-header
        --convert-tabs
        --min-conditional-indent=0
        --indent=spaces=4
        --close-templates
        --add-brackets
        --break-after-logical
        ${CHECK_FILES}
    )

    IF(NOT WIN32 STREQUAL "1")
        ADD_CUSTOM_TARGET(
            format
            COMMAND ${CMAKE_BINARY_DIR}/bin/astyle ${ASTYLE_ARGS}
            COMMENT "running astyle"
        )
    ELSE()
        ADD_CUSTOM_TARGET(
            format
            COMMAND ${CMAKE_BINARY_DIR}/bin/astyle.exe ${ASTYLE_ARGS}
            COMMENT "running astyle"
        )
    ENDIF()

ENDIF()

# ------------------------------------------------------------------------------
# Clang Tidy
# ------------------------------------------------------------------------------

IF(ENABLE_CLANG_TIDY)

    FIND_PROGRAM(CLANG_TIDY_BIN clang-tidy)
    FIND_PROGRAM(RUN_CLANG_TIDY_BIN run-clang-tidy.py
        PATHS /usr/share/clang
    )

    IF(CLANG_TIDY_BIN STREQUAL "CLANG_TIDY_BIN-NOTFOUND")
        MESSAGE(FATAL_ERROR "unable to locate clang-tidy")
    ENDIF()

    IF(RUN_CLANG_TIDY_BIN STREQUAL "RUN_CLANG_TIDY_BIN-NOTFOUND")
        MESSAGE(FATAL_ERROR "unable to locate run-clang-tidy.py")
    ENDIF()

    SET(FILTER_REGEX "^((?!Kernel).)*$$")

    LIST(APPEND RUN_CLANG_TIDY_BIN_ARGS
        -clang-tidy-binary ${CLANG_TIDY_BIN}
        -header-filter="${FILTER_REGEX}"
        -checks=clan*,cert*,misc*,perf*,cppc*,read*,mode*,-cert-err58-cpp,-misc-noexcept-move-constructor
    )

    ADD_CUSTOM_TARGET(
        tidy
        COMMAND ${RUN_CLANG_TIDY_BIN} ${RUN_CLANG_TIDY_BIN_ARGS} ${TIDY_SOURCES}
        COMMENT "running clang tidy"
    )

    ADD_CUSTOM_TARGET(
        tidy_list
        COMMAND ${RUN_CLANG_TIDY_BIN} ${RUN_CLANG_TIDY_BIN_ARGS} -export-fixes=tidy.fixes -style=file ${TIDY_SOURCES}
        COMMENT "running clang tidy"
    )

ENDIF()

# ------------------------------------------------------------------------------
# CppCheck
# ------------------------------------------------------------------------------

IF(ENABLE_CPPCHECK)

    LIST(APPEND CPPCHECK_CMAKE_ARGS
        "-DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}"
    )

    EXTERNALPROJECT_ADD(
        cppcheck
        GIT_REPOSITORY      https://github.com/danmar/cppcheck.git
        GIT_TAG             1.79
        GIT_SHALLOW         1
        CMAKE_ARGS          ${CPPCHECK_CMAKE_ARGS}
        PREFIX              ${CMAKE_BINARY_DIR}/external/cppcheck/prefix
        TMP_DIR             ${CMAKE_BINARY_DIR}/external/cppcheck/tmp
        STAMP_DIR           ${CMAKE_BINARY_DIR}/external/cppcheck/stamp
        DOWNLOAD_DIR        ${CMAKE_BINARY_DIR}/external/cppcheck/download
        SOURCE_DIR          ${CMAKE_BINARY_DIR}/external/cppcheck/src
        BINARY_DIR          ${CMAKE_BINARY_DIR}/external/cppcheck/build
    )

    LIST(APPEND CPPCHECK_ARGS
        --enable=warning,style,performance,portability
        --suppress=arithOperationsOnVoidPointer
        --std=c99
        --verbose
        --error-exitcode=1
        --language=c
        --xml
        --inline-suppr
        -DMAIN=main
        -I ${CHECK_FILES}
    )

    ADD_CUSTOM_TARGET(
        check
        COMMAND ${CMAKE_BINARY_DIR}/bin/cppcheck ${CPPCHECK_ARGS}
        COMMENT "running cppcheck"
    )

ENDIF()
