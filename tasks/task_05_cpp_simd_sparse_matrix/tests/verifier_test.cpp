#include "spmv.hpp"
#include <iostream>
#include <cassert>
#include <cmath>
#include <chrono>
#include <random>

void test_dimension_validation() {
    CSRMatrix m;
    m.num_rows = 2;
    m.num_cols = 2;
    m.row_ptrs = {0, 1}; // Invalid: size must be num_rows + 1 = 3
    m.values = {1.0};
    m.col_indices = {0};

    std::vector<double> x = {1.0, 2.0};
    bool caught = false;
    try {
        spmv_multiply(m, x);
    } catch (const std::invalid_argument&) {
        caught = true;
    }
    assert(caught && "Must reject mismatched row_ptrs dimensions");
    std::cout << "[PASS] Tier 1: Dimension Validation Guard" << std::endl;
}

void test_numerical_correctness() {
    // 3x3 Matrix:
    // [10  0  20]
    // [ 0 30   0]
    // [ 0  0  40]
    CSRMatrix m;
    m.num_rows = 3;
    m.num_cols = 3;
    m.row_ptrs = {0, 2, 3, 4};
    m.col_indices = {0, 2, 1, 2};
    m.values = {10.0, 20.0, 30.0, 40.0};

    std::vector<double> x = {1.0, 2.0, 3.0};
    // Expected y = [10*1 + 20*3, 30*2, 40*3] = [70, 60, 120]
    std::vector<double> y = spmv_multiply(m, x);

    assert(std::abs(y[0] - 70.0) < 1e-6);
    assert(std::abs(y[1] - 60.0) < 1e-6);
    assert(std::abs(y[2] - 120.0) < 1e-6);
    std::cout << "[PASS] Tier 2: Numerical Correctness Invariant" << std::endl;
}

void test_large_scale_benchmark() {
    const size_t rows = 5000;
    const size_t cols = 5000;
    const size_t nnz_per_row = 30; // 150,000 non-zero elements

    CSRMatrix m;
    m.num_rows = rows;
    m.num_cols = cols;
    m.row_ptrs.resize(rows + 1);

    std::mt19937_64 rng(1337);
    std::uniform_real_distribution<double> dist(0.1, 10.0);
    std::uniform_int_distribution<size_t> col_dist(0, cols - 1);

    m.row_ptrs[0] = 0;
    for (size_t i = 0; i < rows; ++i) {
        for (size_t k = 0; k < nnz_per_row; ++k) {
            m.col_indices.push_back(col_dist(rng));
            m.values.push_back(dist(rng));
        }
        m.row_ptrs[i + 1] = m.values.size();
    }

    std::vector<double> x(cols, 1.0);

    auto start = std::chrono::high_resolution_clock::now();
    std::vector<double> y = spmv_multiply(m, x);
    auto end = std::chrono::high_resolution_clock::now();

    double elapsed_ms = std::chrono::duration<double, std::milli>(end - start).count();
    assert(y.size() == rows);
    std::cout << "[PASS] Tier 3: High-Scale Benchmark (" << m.values.size() 
              << " non-zeros in " << elapsed_ms << " ms)" << std::endl;
}

int main() {
    std::cout << "=== Running Task 05 C++ SpMV Verifiers ===" << std::endl;
    test_dimension_validation();
    test_numerical_correctness();
    test_large_scale_benchmark();
    std::cout << "All C++ verifier tiers passed successfully!" << std::endl;
    return 0;
}
