# Task 05: SIMD-Optimized Compressed Sparse Row Matrix Multiplication

## Domain
High-Performance Computing, Cache-Line Optimization & SIMD Vectorization in C++20

## Context & Problem Description
You are optimizing a core linear algebra kernel for a deep learning inference engine. The kernel performs Sparse Matrix-Vector Multiplication (SpMV):
$$y = A \cdot x$$
where matrix $A \in \mathbb{R}^{M \times N}$ is stored in Compressed Sparse Row (CSR) format:
* `values`: non-zero scalar values
* `col_indices`: column index for each non-zero value
* `row_ptrs`: index pointers to the start of each row (size $M + 1$)

The naive scalar baseline implementation in `src/spmv.cpp` suffers from severe memory latency and pipeline stalls:
1. **Cache Thrashing:** Random indirect indexing `x[col_indices[j]]` causes severe L1/L2 cache misses on large matrices.
2. **Pipeline Stalls:** Short row loops inhibit CPU instruction-level parallelism (ILP) and prevent modern compilers from generating vectorized AVX2/FMA instructions.
3. **Missing Dimension Guards:** Accessing out-of-bound dimensions triggers undefined behavior and segmentation faults.

## Requirements
Refactor `src/spmv.cpp` to fulfill:
1. **Dimension Validation:**
   - Verify that `row_ptrs.size() == num_rows + 1`, `values.size() == col_indices.size()`, and `x.size() == num_cols`. If mismatched, throw `std::invalid_argument`.
2. **Loop Unrolling & Vectorization:**
   - Optimize the inner row product utilizing 4-way or 8-way loop unrolling and Fused Multiply-Add (FMA) patterns to maximize register reuse.
3. **Numerical Invariant:**
   - Ensure maximum absolute error relative to analytical ground truth does not exceed $\epsilon \le 10^{-6}$.
4. **Performance Target:**
   - Achieve at least a $2.5\times$ speedup over the unoptimized baseline on a test matrix with $\ge 100,000$ non-zero elements.

## Verification
The CMake test runner validates:
* Dimensional mismatch exceptions and zero-row edge cases.
* Numerical accuracy against reference dense matrix multiplication.
* High-volume throughput benchmark measuring execution wall-clock time.
