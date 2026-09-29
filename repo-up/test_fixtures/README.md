# test_fixtures/README.md

These directories contain **deliberately bad code** used as test inputs for the
repo-up analysis pipeline. They are intentional bad-practice examples and are
**not representative of production code**.

## Fixture contents

| Directory | Purpose |
|---|---|
| `fixture_python_ts/` | Python + TypeScript fixture with hardcoded secrets, eval usage, circular imports, god class, missing error handling |
| `fixture_java/` | Java fixture for testing Java AST parsing and class metrics |
| `fixture_cpp/` | C++ fixture for testing C++ AST parsing |
| `demo_taskflow/` | A fuller project fixture demonstrating the complete analysis flow |

## Secrets & credentials

Any API keys, tokens, or credentials that appear in these fixtures are
**entirely fake and were generated for testing purposes only**. They carry no
access to any real system and must never be treated as real credentials.

Examples of fake values you will find:
- `AKIAABCDEFGHIJKLMNOP` — fake AWS Access Key ID (does not grant any access)
- `sk-fake1234567890` — fake API token

Do not replace or redact these values — they are required to trigger the
secret-detection rules in the test suite.
