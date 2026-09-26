#include "spmv.hpp"
#include <immintrin.h>

std::vector<double> spmv_multiply(const CSRMatrix& matrix, const std::vector<double>& x) {
    // 1. Dimension Validation
    if (matrix.row_ptrs.size() != matrix.num_rows + 1) {
        throw std::invalid_argument("row_ptrs size must equal num_rows + 1");
    }
    if (matrix.values.size() != matrix.col_indices.size()) {
        throw std::invalid_argument("values and col_indices sizes must match");
    }
    if (x.size() != matrix.num_cols) {
        throw std::invalid_argument("vector x size must equal matrix num_cols");
    }

    std::vector<double> y(matrix.num_rows, 0.0);

    const double* const __restrict vals = matrix.values.data();
    const size_t* const __restrict cols = matrix.col_indices.data();
    const size_t* const __restrict r_ptrs = matrix.row_ptrs.data();
    const double* const __restrict x_vec = x.data();
    double* const __restrict y_out = y.data();

    // 2. Loop unrolling with accumulator variables to expose instruction-level parallelism
    for (size_t i = 0; i < matrix.num_rows; ++i) {
        const size_t row_start = r_ptrs[i];
        const size_t row_end = r_ptrs[i + 1];
        const size_t len = row_end - row_start;

        double sum0 = 0.0;
        double sum1 = 0.0;
        double sum2 = 0.0;
        double sum3 = 0.0;

        size_t j = row_start;
        // 4-way unrolling
        for (; j + 3 < row_end; j += 4) {
            sum0 += vals[j + 0] * x_vec[cols[j + 0]];
            sum1 += vals[j + 1] * x_vec[cols[j + 1]];
            sum2 += vals[j + 2] * x_vec[cols[j + 2]];
            sum3 += vals[j + 3] * x_vec[cols[j + 3]];
        }

        // Remainder loop
        double remainder = 0.0;
        for (; j < row_end; ++j) {
            remainder += vals[j] * x_vec[cols[j]];
        }

        y_out[i] = (sum0 + sum1) + (sum2 + sum3) + remainder;
    }

    return y;
}
