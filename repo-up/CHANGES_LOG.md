## Phase 3: Security Smell and CWE Identification Engine
- Restructured `backend/analysis/rules/security/` into a Python package containing 5 new structured security rules.
- **SEC-CWE-502**: Implemented unsafe deserialization detection covering `pickle`, `marshal`, `shelve`, unsafe `yaml.load` (Python), `node-serialize` (JS/TS), and `ObjectInputStream.readObject` (Java).
- **SEC-WEAK-CRYPTO**: Implemented weak cryptographic hash detection (CWE-327) covering MD5 and SHA-1 API calls in Python (`hashlib`), Java (`MessageDigest`), JS/TS (`crypto`), and C++ (`OpenSSL`).
- **SEC-UNSAFE-ASSERT**: Implemented heuristic detection for Python `assert` statements used as security boundaries (CWE-617 proxy).
- **SEC-DANGEROUS-EXEC**: Implemented command injection / dynamic execution detection (CWE-78/95) across all 5 languages (e.g. `eval`, `exec`, `os.system`, `child_process.exec`, `Runtime.exec`, `system`).
- **SEC-CWE-703**: Refined exception handling checks to look for specific risky operations (I/O, network, database) *not* enclosed in a `try/except` (or `try/catch`) block, using AST parent traversal for Python, JS/TS, and Java.
- **SEC-HARDCODED-SECRET**: Normalized the secret detector into the new finding structure with 7 distinct shape-based patterns. Secret values are fully redacted from finding descriptions. Added detection for committed `.env` files (SEC-COMMITTED-ENV).
- Integrated the new `security_engine.py` as Stage 9 in `analyze.py`, with penalties soft-capped at 40 points total.
- Registered all 7 new rules in `rule_registry.py` with CWE mappings.
- Created multi-language security fixtures and a comprehensive `validate_security.py` integration test. All 11 tests, including safe-counterpart false-positive checks, pass successfully.

---

### Phase 3 Final Report

#### 1. Rules Implemented & CWE Mappings
| Rule ID | Name | CWE |
| :--- | :--- | :--- |
| **SEC-CWE-502** | Unsafe Deserialization | CWE-502 |
| **SEC-WEAK-CRYPTO** | Weak Cryptographic Hash | CWE-327 |
| **SEC-UNSAFE-ASSERT** | Unsafe Assert as Security Boundary | CWE-617 |
| **SEC-DANGEROUS-EXEC** | Dangerous Code/Command Execution | CWE-78 / CWE-95 |
| **SEC-CWE-703** | Missing Exception Handling | CWE-703 |
| **SEC-HARDCODED-SECRET** | Hardcoded Secret | CWE-798 |
| **SEC-COMMITTED-ENV** | Committed Environment File | CWE-798 |

#### 2. Supported Languages & Detection Methods
- **SEC-CWE-502**: Python (`pickle`, `marshal`, `shelve`, unsafe `yaml.load`), Java (`readObject`), JS/TS (`node-serialize` imports). Uses AST traversal to find method calls and kwargs.
- **SEC-WEAK-CRYPTO**: Python, Java, JS/TS, C++. Detects actual API calls for MD5 and SHA-1 (e.g., `hashlib.md5`, `crypto.createHash('sha1')`, OpenSSL `EVP_md5`).
- **SEC-UNSAFE-ASSERT**: Python. Heuristic keyword match (e.g., "auth", "admin", "token") within the test expression of `assert` statements. Skips test files.
- **SEC-DANGEROUS-EXEC**: Python, JS/TS, Java, C++. Detects dynamic eval (`eval`, `new Function`) and shell execution (`os.system`, `subprocess(shell=True)`, `child_process.exec`, `Runtime.exec`, `system()`).
- **SEC-CWE-703**: Python, JS/TS, Java. Uses AST parent traversal to verify if risky operations (I/O, network, database API calls) are syntactically enclosed in a `try` block.
- **SEC-HARDCODED-SECRET / SEC-COMMITTED-ENV**: All languages. Uses shape-based regex patterns line-by-line. Extracts location but strictly **redacts** the secret value from the finding description to prevent leakage.

#### 3. Fixtures & Tests
- Added `test_fixtures/fixture_python_ts/src/sec_bad.py` and `sec_bad.ts` containing intentional vulnerabilities and their safe counterparts.
- Added `validate_security.py` integration test.
- **Results**: All 11 checks pass. The safe counterparts do not trigger false positives (except if intentionally invoking a flagged I/O without try/catch). Existing Phase 1 tests pass. Frontend builds successfully.

#### 4. Known Limitations & False Positives
- **CWE-502**: Cannot prove taint flow. `yaml.load` with a safe loader is excluded, but standard `pickle` is always flagged as unsafe.
- **Weak Crypto**: Weak hashes used for non-security checksums are flagged. MD5 in text strings outside API calls is not flagged.
- **Unsafe Assert**: Heuristic matching will flag non-security assertions if they use keywords like "auth". Test files are excluded to mitigate this.
- **CWE-703**: Syntactic checking only. A `try` block catching `MemoryError` around a network call is considered "covered". Broad `except` clauses are not penalized here.
- **Secrets**: Entropy-based detection is missing; currently limited to regex shapes.

#### 5. Intentionally Deferred Items
- C++ Exception Handling and Unsafe Deserialization (requires deep semantic/type resolution).
- Automated fixes, sandbox execution, LLM-based repairs, and CodeQL integration.

---

### Phase 4 Final Report (Cross-Language Parity)

#### 1. Capability Matrix
The rule engine now tracks explicit support (`backend/analysis/cross_language/capability_matrix.py`). Example highlights:
- **Full Support**: `CODE-LONG-LINE`, `SEC-HARDCODED-SECRET` (text based).
- **Python / JS / TS**: Almost complete AST support for all smells and security checks (except TS/JS `CODE-UNDEFINED-NAME` being partial due to dynamic `require()`).
- **Java**: Full structural and security support. `CODE-UNDEFINED-NAME` disabled (requires semantic type-resolution).
- **C++**: AST supported for code smells (`CODE-LONG-LINE`, `CODE-DUPLICATE-BLOCK`). Security rules partially supported via API signature (e.g., `system()`, OpenSSL `EVP_md5`). `CODE-UNDEFINED-NAME` disabled (infeasible due to macros/includes without a compiler).

#### 2. Fixed Bugs
- **JS/TS False Positives**: `CODE-UNDEFINED-NAME` was incorrectly flagging function parameters and local variables in JS/TS. Created `_js_all_locals` to merge `formal_parameters`, `lexical_declaration`, and `catch_clause` into the scope.
- **JS Built-ins**: Added `eval` to `_JS_GLOBALS` so the security engine can correctly catch it.
- **Empty Repo Safety**: Configured `scorer.py` and metric fallbacks to prevent `ZeroDivisionError` when a repository has 0 parseable files.

#### 3. Unsupported / Partial Cases
- **Java/C++ `CODE-UNDEFINED-NAME`**: Requires a full semantic phase or compiler to track imports, inner classes, and namespaces reliably. Disabled to prevent massive false positives.
- **Java/C++ `CODE-INCONSISTENT-RETURN`**: These languages declare return types at the method level. A bare `return;` in a non-void method is a compiler type error, not an AST-level smell, so this is skipped.
- **C++ Exception Handling / Deserialization**: Lacks standard library enforcement for deserialization (unlike `pickle` / `ObjectInputStream`), and C++ exception tracing requires semantic graph resolution. 

#### 4. Fixture Results & Parser Failures
- Run on `python`, `javascript`, `typescript`, `java`, `cpp` cross-language fixtures.
- **Parse Success**: 100% (14/14 ASTs generated).
- **Security Findings**: Found all injected issues (CWE-502, CWE-703, CWE-78/95, CWE-327, CWE-617) appropriately across the corresponding languages.
- **Metric Scoring**: `validate_parity.py` proves that all scores are deterministic and safely bounded (0-100).

#### 5. Remaining Cross-Language Limitations
The platform's static AST approach is extremely fast but inherently limited by the lack of *type resolution* and *taint analysis*. To close the remaining gap for Java and C++, the parser would need integration with semantic indexing (like LSIF or compile_commands.json). No repair or LLM features were implemented.

---

### Phase 5 Final Report (Rule-Based Resolution and Safe Auto-Fix Engine)

#### 1. Repairs Implemented
- **Tier 1 (Deterministic Auto-Fix)**:
  - Python: `yaml.load` → `yaml.safe_load` (`SEC-CWE-502`)
  - Python: `hashlib.md5`/`sha1` → `sha256` (`SEC-WEAK-CRYPTO`)
  - JS/TS: `crypto.createHash('md5'/'sha1')` → `sha256` (`SEC-WEAK-CRYPTO`)
  - Java: `MessageDigest.getInstance("MD5"/"SHA-1")` → `"SHA-256"` (`SEC-WEAK-CRYPTO`)
- **Tier 2 (Suggested)**:
  - Java Deserialization (`SEC-CWE-502`)
  - Python / JS Code Execution (`SEC-DANGEROUS-EXEC`)
- **Tier 3 (Explanation)**:
  - Python Unsafe Assert (`SEC-UNSAFE-ASSERT`)
  - Multi-Language Missing Exception Handling (`SEC-CWE-703`)

#### 2. Supported Languages for Auto-Fix
- Python
- JavaScript
- TypeScript
- Java

#### 3. Diff Validation Results
- The API correctly returns a `Patch` object containing unified diffs (e.g. `--- a/file.py \n+++ b/file.py`).
- 5-step strict validation blocks malformed patches (e.g., path escapes, line index out of bounds, AST-breaking edits, original text mismatch).

#### 4. Tests
- Created `backend/validate_repair.py` with 15 granular checks spanning generation, immutability, parseability, and rejection. 18/18 checks pass across all 4 auto-fix capable languages.

#### 5. Known Limitations
- Modifying the original repository files is intentionally disabled (sandbox pending).
- C++ does not currently have a Tier 1 deterministic fix implemented (regex-based C++ substitutions are inherently unsafe without a full semantic compiler).
