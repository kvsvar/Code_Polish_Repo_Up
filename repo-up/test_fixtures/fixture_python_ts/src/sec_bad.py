# sec_bad.py — Intentionally vulnerable Python fixture for Phase 3 security tests
# WARNING: All secrets are FAKE. This code is intentionally bad for testing.

import pickle
import yaml
import hashlib
import subprocess
import os

# --- CWE-502: Unsafe Deserialization ---

def load_user_data(data: bytes):
    # UNSAFE: pickle.loads on attacker-controlled data
    return pickle.loads(data)

def load_config(stream):
    # UNSAFE: yaml.load without SafeLoader
    return yaml.load(stream)

# --- CWE-327: Weak Cryptographic Hash ---

def hash_password(password: str) -> str:
    # UNSAFE: MD5 for password hashing
    return hashlib.md5(password.encode()).hexdigest()

def checksum(data: bytes) -> str:
    # UNSAFE: SHA-1
    return hashlib.sha1(data).hexdigest()

# --- CWE-78: Dangerous Command Execution ---

def run_command(user_input: str):
    # UNSAFE: os.system with user input
    os.system(f"ls {user_input}")

def run_subprocess(cmd: str):
    # UNSAFE: subprocess with shell=True
    subprocess.run(cmd, shell=True)

def run_eval(expr: str):
    # UNSAFE: eval on arbitrary input
    return eval(expr)

# --- CWE-617: Unsafe Assert ---

def check_admin(user_role: str):
    # UNSAFE: assert for security boundary
    assert user_role == "admin", "Must be admin"
    return "admin_panel_data"

def authorize_access(token: str, required_permission: str):
    # UNSAFE: assert for authorization
    assert token == "valid_token", "Unauthorized"
    return True

# --- CWE-703: Missing Exception Handling ---

def fetch_data(url: str):
    # UNSAFE: network call without try/except
    import requests
    response = requests.get(url)
    return response.json()

def read_file(path: str):
    # UNSAFE: file open without try/except
    f = open(path, "r")
    return f.read()

# --- CWE-798: Hardcoded Secrets (FAKE values) ---
FAKE_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
FAKE_API_KEY = "api_key = 'x7kP9mNqR2wL5vB8tH3jE6yF1cA4dG0'"
DATABASE_URL = "postgresql://admin:password123@localhost/mydb"

# --- Safe counterparts (should NOT be flagged) ---

def safe_hash(data: bytes) -> str:
    """SHA-256 is safe."""
    return hashlib.sha256(data).hexdigest()

def safe_subprocess(cmd_parts: list):
    """No shell=True, list args — safe."""
    try:
        result = subprocess.run(cmd_parts, shell=False, capture_output=True)
        return result.stdout
    except Exception as e:
        return str(e)

def safe_yaml_load(stream):
    """safe_load is safe."""
    return yaml.safe_load(stream)

def safe_pickle_alternative(data: str):
    """JSON is safe for data exchange."""
    import json
    return json.loads(data)
