# Python cross-language fixture — clean.py
# Conceptually equivalent to the other language clean fixtures.
# Contains: one class, two methods, proper exception handling, strong crypto.


import hashlib


class UserService:
    """Manages user authentication (clean, no smells)."""

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate a user with a secure hash."""
        digest = hashlib.sha256(password.encode()).hexdigest()
        return self._lookup(username, digest)

    def _lookup(self, username: str, digest: str) -> bool:
        """Internal lookup against credential store."""
        try:
            # Simulated store access
            stored = self._store.get(username)
            return stored == digest
        except Exception:
            return False

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
