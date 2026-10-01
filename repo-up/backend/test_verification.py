"""
backend/test_verification.py - Malicious and boundary tests for Phase 6 Sandbox Verification.
"""
import os
import unittest
from analysis.finding import Finding
from analysis.repair.patch_model import Patch, PatchValidationError
from verification.sandbox import VerificationSandbox
from verification.runner import verify_patch
from verification.result import VerificationStatus

class TestSandboxVerification(unittest.TestCase):
    def setUp(self):
        # We use the current backend directory as a dummy project root for tests
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.dummy_finding = Finding(
            rule_id="SEC-TEST",
            category="Security",
            title="Test",
            description="Test finding",
            severity="High",
            file="main.py"
        )
        
    def test_path_traversal_rejection(self):
        """Ensure patches modifying files outside the workspace are rejected."""
        patch = Patch(
            rule_id="SEC-TEST",
            language="Python",
            tier="tier1_deterministic",
            file="../../../../../../Windows/System32/cmd.exe",
            start_line=1, start_col=0, end_line=1, end_col=0,
            old_text="", new_text="malicious", description="Escape"
        )
        result = verify_patch(self.project_root, patch, self.dummy_finding)
        self.assertEqual(result.status, VerificationStatus.FAIL_PARSE)
        self.assertIn("traversal", result.message.lower())

    def test_malformed_patch_bounds(self):
        """Ensure patches with line indices out of bounds are rejected."""
        patch = Patch(
            rule_id="SEC-TEST",
            language="Python",
            tier="tier1_deterministic",
            file="main.py",
            start_line=99999, start_col=0, end_line=99999, end_col=0,
            old_text="", new_text="malicious", description="OOB"
        )
        result = verify_patch(self.project_root, patch, self.dummy_finding)
        self.assertEqual(result.status, VerificationStatus.FAIL_PARSE)
        self.assertIn("bounds", result.message.lower())

    def test_parser_failure(self):
        """Ensure patches that break the AST are rejected (FAILED_PARSE)."""
        # We need a file that exists. Let's patch main.py with invalid python.
        with open(os.path.join(self.project_root, "main.py"), "r") as f:
            lines = f.readlines()
            old_first_line = lines[0]
            
        patch = Patch(
            rule_id="SEC-TEST",
            language="Python",
            tier="tier1_deterministic",
            file="main.py",
            start_line=1, start_col=0, end_line=1, end_col=0, # Replace line 1
            old_text=old_first_line, 
            new_text="def foo(:::: syntax error\n", 
            description="Break AST"
        )
        result = verify_patch(self.project_root, patch, self.dummy_finding)
        self.assertEqual(result.status, VerificationStatus.FAIL_PARSE)
        self.assertIn("parse error", result.message.lower())

if __name__ == "__main__":
    unittest.main()
