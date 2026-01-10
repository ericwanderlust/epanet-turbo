cmake_minimum_required(VERSION 3.20)
project(EPANET C)

option(BUILD_SERIAL "Build serial EPANET engine (no OpenMP)" ON)
option(ENABLE_OPENMP "Build OpenMP EPANET engine" ON)
option(BUILD_TESTS "Build tests (requires Boost)" OFF)

# Common Sources
set(EPANET_SOURCES
    src/epanet2.c
    src/epanet.c
    src/hydraul.c
    src/hydsolver.c
    src/hydcoeffs.c
    src/hydstatus.c
    src/inpfile.c
    src/input1.c
    src/input2.c
    src/input3.c
    src/leakage.c
    src/output.c
    src/project.c
    src/quality.c
    src/qualreact.c
    src/qualroute.c
    src/report.c
    src/rules.c
    src/smatrix.c
    src/validate.c
    src/epanet_turbo.c
    src/epanet_bulk.c
    src/mempool.c
    src/flowbalance.c
    src/genmmd.c
    src/hash.c
)

# Configuration Helper
function(configure_common target_name)
    target_include_directories(${target_name} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
    target_compile_features(${target_name} PRIVATE c_std_11)
    set_target_properties(${target_name} PROPERTIES POSITION_INDEPENDENT_CODE ON)
    
    if(MSVC)
        target_compile_definitions(${target_name} PRIVATE _CRT_SECURE_NO_WARNINGS _CRT_SECURE_NO_DEPRECATE)
        target_compile_options(${target_name} PRIVATE /fp:precise)
    else()
        target_compile_options(${target_name} PRIVATE -Wall -Wextra -Wno-unused-parameter)
    endif()
    
    # Export Definition (dllexport handled by epanet_turbo_export.h or epanet2.h macros usually, 
    # but we can add standard defs here if needed)
endfunction()

# 1. Serial Target
if(BUILD_SERIAL)
    add_library(epanet2 SHARED ${EPANET_SOURCES})
    configure_common(epanet2)
    target_compile_definitions(epanet2 PRIVATE EPNT_SERIAL=1 EPANET_EXPORTS)
    
    if(MSVC)
         # Existing def for consistent exports if headers depend on it?
         # epanet2.c often relies on declspec.
    endif()
    
    set_target_properties(epanet2 PROPERTIES OUTPUT_NAME "epanet2")
    install(TARGETS epanet2 DESTINATION .)
endif()

# 2. OpenMP Target
if(ENABLE_OPENMP)
    find_package(OpenMP)
    if(OpenMP_C_FOUND)
        add_library(epanet2_openmp SHARED ${EPANET_SOURCES})
        configure_common(epanet2_openmp)
        target_link_libraries(epanet2_openmp PRIVATE OpenMP::OpenMP_C)
        target_compile_definitions(epanet2_openmp PRIVATE EPNT_OPENMP=1 epanet2_EXPORTS EPANET_EXPORTS)
        
        # Ensure distinct name
        set_target_properties(epanet2_openmp PROPERTIES OUTPUT_NAME "epanet2_openmp")
        install(TARGETS epanet2_openmp DESTINATION .)
    else()
        message(WARNING "OpenMP not found. epanet2_openmp will not be built.")
    endif()
endif()

# Install Headers
install(FILES include/epanet2.h DESTINATION include)
install(FILES include/epanet2_2.h DESTINATION include)
install(FILES include/epanet2_enums.h DESTINATION include)
install(FILES include/epanet_turbo.h DESTINATION include)
install(FILES include/epanet_bulk.h DESTINATION include)

# Tests (Optional)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
