#pragma once

#include <vector>
#include <cstddef>
#include <stdexcept>

struct CSRMatrix {
    size_t num_rows;
    size_t num_cols;
    std::vector<double> values;
    std::vector<size_t> col_indices;
    std::vector<size_t> row_ptrs;
};

/**
 * High-performance sparse matrix-vector multiplication: y = A * x
 */
std::vector<double> spmv_multiply(const CSRMatrix& matrix, const std::vector<double>& x);
