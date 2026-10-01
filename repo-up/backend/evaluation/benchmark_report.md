# Repo-Up Five-Language Cross-Language Benchmark

## Language Comparison
| Language | Repositories | Expected | Detected | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| Python | 5 | 4 | 31 | 2 | 29 | 2 | 0.06 | 0.50 | 0.11 |
| Javascript | 5 | 4 | 30 | 3 | 27 | 1 | 0.10 | 0.75 | 0.18 |
| Typescript | 5 | 4 | 30 | 3 | 27 | 1 | 0.10 | 0.75 | 0.18 |
| Java | 5 | 4 | 32 | 3 | 29 | 1 | 0.09 | 0.75 | 0.17 |
| Cpp | 5 | 4 | 30 | 3 | 27 | 1 | 0.10 | 0.75 | 0.18 |

## Parser Reliability
- **Files Discovered**: 25 (Synthesized)
- **Files Parsed**: 25
- **Parse Failures**: 0
- **Unsupported Constructs**: 0
- **Analysis Failures**: 0

## Security Subset
| Rule/CWE | Language | Expected | Detected | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| SEC-AST-MISSING-ERRHANDLING | Python | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-DANGEROUS-EXEC | Python | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-DANGEROUS-EXEC | Javascript | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-DANGEROUS-EXEC | Typescript | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-DANGEROUS-EXEC | Java | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-DANGEROUS-EXEC | Cpp | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-CWE-703 | Python | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-EVAL-EXEC | Python | 1 | 0 | 0.00 | 0.00 | 0.00 |
| SEC-EVAL-EXEC | Javascript | 1 | 0 | 0.00 | 0.00 | 0.00 |
| SEC-EVAL-EXEC | Typescript | 1 | 0 | 0.00 | 0.00 | 0.00 |
| SEC-EVAL-EXEC | Java | 1 | 0 | 0.00 | 0.00 | 0.00 |
| SEC-EVAL-EXEC | Cpp | 1 | 0 | 0.00 | 0.00 | 0.00 |
| SEC-WEAK-CRYPTO | Python | 1 | 0 | 0.00 | 0.00 | 0.00 |
| SEC-WEAK-CRYPTO | Javascript | 1 | 1 | 1.00 | 1.00 | 1.00 |
| SEC-WEAK-CRYPTO | Typescript | 1 | 1 | 1.00 | 1.00 | 1.00 |
| SEC-WEAK-CRYPTO | Java | 1 | 1 | 1.00 | 1.00 | 1.00 |
| SEC-WEAK-CRYPTO | Cpp | 1 | 1 | 1.00 | 1.00 | 1.00 |
| SEC-AST-EVAL-EXEC | Javascript | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-AST-EVAL-EXEC | Typescript | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-AST-EVAL-EXEC | Java | 0 | 1 | 0.00 | 0.00 | 0.00 |
| SEC-AST-EVAL-EXEC | Cpp | 0 | 1 | 0.00 | 0.00 | 0.00 |

## Reproducibility
Command to regenerate this benchmark report:
`python backend/run_cross_language_benchmark.py`