include(ExternalProject)
find_package(Git REQUIRED)

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

if(ALL_CHECKS)
    SET(ENABLE_ASTYLE ON)
    SET(ENABLE_CLANG_TIDY ON)
    SET(ENABLE_CPPCHECK ON)
endif()

# ------------------------------------------------------------------------------
# Git whitespace
# ------------------------------------------------------------------------------


add_custom_target(
    commit
    COMMAND echo COMMAND ${GIT_EXECUTABLE} diff --check HEAD^
    COMMENT "Running git check"
)

# ------------------------------------------------------------------------------
# Astyle
# ------------------------------------------------------------------------------

if(ENABLE_ASTYLE)

    list(APPEND ASTYLE_CMAKE_ARGS
        "-DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}"
    )

    ExternalProject_Add(
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

    list(APPEND ASTYLE_ARGS
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

    if(NOT WIN32 STREQUAL "1")
        add_custom_target(
            format
            COMMAND ${CMAKE_BINARY_DIR}/bin/astyle ${ASTYLE_ARGS}
            COMMENT "running astyle"
        )
    else()
        add_custom_target(
            format
            COMMAND ${CMAKE_BINARY_DIR}/bin/astyle.exe ${ASTYLE_ARGS}
            COMMENT "running astyle"
        )
    endif()

endif()

# ------------------------------------------------------------------------------
# Clang Tidy
# ------------------------------------------------------------------------------

if(ENABLE_CLANG_TIDY)

    find_program(CLANG_TIDY_BIN clang-tidy)
    find_program(RUN_CLANG_TIDY_BIN run-clang-tidy.py
        PATHS /usr/share/clang
    )

    if(CLANG_TIDY_BIN STREQUAL "CLANG_TIDY_BIN-NOTFOUND")
        message(FATAL_ERROR "unable to locate clang-tidy")
    endif()

    if(RUN_CLANG_TIDY_BIN STREQUAL "RUN_CLANG_TIDY_BIN-NOTFOUND")
        message(FATAL_ERROR "unable to locate run-clang-tidy.py")
    endif()

    SET(FILTER_REGEX "^((?!Kernel).)*$$")

    list(APPEND RUN_CLANG_TIDY_BIN_ARGS
        -clang-tidy-binary ${CLANG_TIDY_BIN}
        -header-filter="${FILTER_REGEX}"
        -checks=clan*,cert*,misc*,perf*,cppc*,read*,mode*,-cert-err58-cpp,-misc-noexcept-move-constructor
    )

    add_custom_target(
        tidy
        COMMAND ${RUN_CLANG_TIDY_BIN} ${RUN_CLANG_TIDY_BIN_ARGS} ${TIDY_SOURCES}
        COMMENT "running clang tidy"
    )

    add_custom_target(
        tidy_list
        COMMAND ${RUN_CLANG_TIDY_BIN} ${RUN_CLANG_TIDY_BIN_ARGS} -export-fixes=tidy.fixes -style=file ${TIDY_SOURCES}
        COMMENT "running clang tidy"
    )

endif()

# ------------------------------------------------------------------------------
# CppCheck
# ------------------------------------------------------------------------------

if(ENABLE_CPPCHECK)

    list(APPEND CPPCHECK_CMAKE_ARGS
        "-DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}"
    )

    ExternalProject_Add(
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

    list(APPEND CPPCHECK_ARGS
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

    add_custom_target(
        check
        COMMAND ${CMAKE_BINARY_DIR}/bin/cppcheck ${CPPCHECK_ARGS}
        COMMENT "running cppcheck"
    )

endif()
