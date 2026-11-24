cmake_minimum_required(VERSION 3.10)

project(RISCV-Simulator)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_FLAGS "-O2 -Wall")

include_directories(${CMAKE_SOURCE_DIR}/include)

add_executable(
    Simulator 
    src/MainCPU.cpp 
    src/FaultConfig.cpp
    src/MemoryManager.cpp 
    src/Simulator.cpp 
    src/BranchPredictor.cpp 
    src/Cache.cpp
)

add_executable(
    CacheSim 
    src/MainCache.cpp 
    src/MemoryManager.cpp 
    src/Cache.cpp
)

add_executable(
    CacheOptimized
    src/MainCacheOptimization.cpp
    src/MemoryManager.cpp
    src/Cache.cpp
)

add_executable(ToDirenoTrace src/ToDirenoTrace.cpp)

include(CTest)
if(BUILD_TESTING)
    add_executable(memory_fault_test test/memory_fault_test.cpp src/MemoryManager.cpp src/Cache.cpp)
    target_include_directories(memory_fault_test PRIVATE ${CMAKE_SOURCE_DIR}/src)
    add_test(NAME memory_fault_test COMMAND memory_fault_test)
    add_executable(cache_fault_test test/cache_fault_test.cpp src/MemoryManager.cpp src/Cache.cpp)
    target_include_directories(cache_fault_test PRIVATE ${CMAKE_SOURCE_DIR}/src)
    add_test(NAME cache_fault_test COMMAND cache_fault_test)
    add_executable(branch_fault_test test/branch_fault_test.cpp src/BranchPredictor.cpp)
    target_include_directories(branch_fault_test PRIVATE ${CMAKE_SOURCE_DIR}/src)
    add_test(NAME branch_fault_test COMMAND branch_fault_test)
    find_package(PythonInterp QUIET)
    if(PYTHONINTERP_FOUND)
        add_test(NAME fault_cli_test COMMAND ${PYTHON_EXECUTABLE}
                 ${CMAKE_SOURCE_DIR}/test/fault_cli_test.py $<TARGET_FILE:Simulator>
                 ${CMAKE_SOURCE_DIR}/kernels/bin/test/test_branch.riscv)
        find_program(RISCV_TEST_GCC riscv64-unknown-elf-gcc)
        if(RISCV_TEST_GCC)
            add_test(NAME memory_kernel_test COMMAND ${PYTHON_EXECUTABLE}
                     ${CMAKE_SOURCE_DIR}/test/memory_kernel_test.py ${RISCV_TEST_GCC}
                     $<TARGET_FILE:Simulator> ${CMAKE_SOURCE_DIR}/kernels/fault-detection/memory_kernel.c
                     ${CMAKE_SOURCE_DIR}/kernels/fault-detection/memory_page_kernel.c
                     ${CMAKE_SOURCE_DIR}/kernels/fault-detection/memory_stride_kernel.c
                     ${CMAKE_SOURCE_DIR}/kernels/start.S)
        endif()
    endif()
endif()
