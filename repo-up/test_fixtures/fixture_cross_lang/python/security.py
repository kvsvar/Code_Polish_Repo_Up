# Python cross-language fixture — security.py
# Conceptually equivalent security issues.
import hashlib, os, pickle


# Weak crypto
def hash_it(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()  # SEC-WEAK-CRYPTO


# Dangerous execution
def run_it(cmd: str) -> None:
    os.system(cmd)  # SEC-DANGEROUS-EXEC


# Unsafe deserialization
def deserialize(data: bytes):
    return pickle.loads(data)  # SEC-CWE-502


# Missing exception handling
def read_data(path: str) -> str:
    f = open(path)  # SEC-CWE-703 — no try/except
    return f.read()


# Unsafe assert as security check
def check_auth(token: str) -> bool:
    assert token == "admin_token", "Unauthorized"  # SEC-UNSAFE-ASSERT
    return True


# Fake secret (FAKE value — do not use)
FAKE_SECRET = "api_key = 'x7kP9mNqR2wL5vB8tH3jE6yF1cA4dG0'"  # SEC-HARDCODED-SECRET
