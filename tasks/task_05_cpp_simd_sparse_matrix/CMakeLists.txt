cmake_minimum_required(VERSION 3.16)
project(Task05_SIMD_SpMV CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(MSVC)
    add_compile_options(/O2 /arch:AVX2)
else()
    add_compile_options(-O3 -march=native -Wall -Wextra)
endif()

include_directories(include)

add_library(spmv_lib src/spmv.cpp)

enable_testing()
add_executable(spmv_verifier tests/verifier_test.cpp)
target_link_libraries(spmv_verifier PRIVATE spmv_lib)

add_test(NAME SpMV_Verifier COMMAND spmv_verifier)
