import abc
from typing import Optional, Dict, Any
import os

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate_explanation(self, context: dict) -> str:
        """
        Returns an explanation string covering:
        1. what was detected
        2. why it matters
        3. relevant evidence
        4. remediation approach
        Must NOT claim verification.
        """
        pass
        
    @abc.abstractmethod
    def generate_patch(self, context: dict) -> Optional[Dict[str, Any]]:
        """
        Returns a structured patch dictionary if applicable, else None.
        {
            "file": str,
            "old_text": str,
            "new_text": str,
            "reason": str
        }
        """
        pass

class DummyProvider(LLMProvider):
    """Fallback provider when no API key is configured."""
    def generate_explanation(self, context: dict) -> str:
        rule = context.get('rule', 'Unknown')
        cwe = context.get('cwe', 'None')
        return (
            f"**AI Explanation (Simulated)**\n\n"
            f"**What:** Detected {rule} (CWE: {cwe}).\n\n"
            f"**Why:** This pattern is generally unsafe or substandard.\n\n"
            f"**Remediation:** Please review the detected region and apply standard best practices. "
            f"Note: This AI-generated suggestion is not yet verified."
        )
        
    def generate_patch(self, context: dict) -> Optional[Dict[str, Any]]:
        # Dummy provider doesn't generate patches, safely returning None.
        # To truly test patch logic, one would implement an active provider.
        return None

def get_provider() -> Optional[LLMProvider]:
    """
    Factory to get the configured LLM provider.
    Returns DummyProvider by default unless configured otherwise.
    """
    if os.environ.get("LLM_PROVIDER") == "dummy":
        return DummyProvider()
    
    # Defaults to DummyProvider since we must not use real APIs without explicit keys.
    return DummyProvider()
