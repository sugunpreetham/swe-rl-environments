# Task 03: Zero-Copy Token Stream Parser & AST Builder

## Domain
Systems Programming, Memory Safety, Compiler Frontend / Lexer-Parser in Rust (2021 Edition)

## Context & Problem Description
You are maintaining a high-throughput, zero-copy Domain Specific Language (DSL) lexer and Abstract Syntax Tree (AST) parser in Rust. The parser evaluates arithmetic and logical expressions embedded in query strings.

The current implementation exhibits three severe vulnerabilities:
1. **Unbounded Recursion Stack Overflow:** Deeply nested sub-expressions (e.g. `((((...))))`) consume the thread stack, crashing the host process with `SIGSEGV` instead of returning a graceful `ParseError::RecursionLimitExceeded`.
2. **Panic on Malformed / Multi-byte UTF-8 Slices:** Slicing raw byte offsets without checking UTF-8 character boundaries panics when encountering emojis or multi-byte unicode tokens in identifiers or strings.
3. **Operator Precedence Bug:** Multiplication/division binding is inverted with addition/subtraction under specific chained parentheses combinations.

## Requirements
Refactor `src/lib.rs` to satisfy:
* **Zero Panic Guarantee:** Under no circumstance should `parse(input)` trigger a runtime panic. All syntax errors, recursion overflows, and unexpected tokens must return a typed `Result<Expr, ParseError>`.
* **Bounded Recursion Depth:** Impose an explicit recursion depth limit of `MAX_DEPTH = 64`. Any depth beyond 64 must return `ParseError::RecursionLimitExceeded`.
* **Unicode & UTF-8 Safety:** Safely tokenize multi-byte UTF-8 identifiers without slice boundary panics.
* **Precise Operator Precedence:** Strictly adhere to standard arithmetic precedence:
  - Factor (parentheses, numbers, identifiers)
  - Term (`*`, `/`)
  - Expression (`+`, `-`)

## Verification
The test suite executes:
- Standard AST expression trees and precedence assertions.
- Deep recursion fuzzing ($>100$ nested parentheses) to verify stack exhaustion protection.
- Fuzz testing with malformed UTF-8 byte streams and random unicode payloads.
- Dynamic property checks verifying mathematical equivalence across permutations.
