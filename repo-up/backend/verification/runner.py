"""
verification/runner.py - Orchestrates candidate patch verification.
"""
from typing import List

from analysis.repair.patch_model import Patch, PatchValidationError
from analysis.finding import Finding
from .sandbox import VerificationSandbox
from .result import VerificationStatus, VerificationResult
from .test_runner import discover_and_run_tests

def verify_patch(original_project_root: str, patch: Patch, original_finding: Finding) -> VerificationResult:
    """
    Executes the verification pipeline for a candidate patch.
    """
    details = {}
    
    try:
        with VerificationSandbox(original_project_root) as sandbox:
            # Stage 1: Patch Application (already validates safe parse via validate_patch)
            try:
                sandbox.apply_patch(patch)
                details["patch"] = "applied cleanly"
            except PatchValidationError as e:
                return VerificationResult(
                    status=VerificationStatus.FAIL_PARSE,
                    parse_result=False,
                    message=str(e),
                    details={"error": "Patch validation or parsing failed"}
                )
            except Exception as e:
                return VerificationResult(
                    status=VerificationStatus.ERROR,
                    parse_result=False,
                    message=str(e),
                    details={"error": "Unexpected error applying patch"}
                )

            # Stage 2: Static / Smell Analysis Verification
            from analysis.rules.smells.smell_engine import run_smell_engine
            from analysis.rules.security.security_engine import run_security_engine
            
            new_smells, _ = run_smell_engine(sandbox.sandbox_root)
            new_security, _ = run_security_engine(sandbox.sandbox_root)
            
            static_pass = True
            security_pass = True
            
            # Re-check the patched file to ensure the finding is actually gone.
            for s in new_smells:
                if s.get("rule_id") == original_finding.rule_id and s.get("file") == original_finding.file:
                    if patch.start_line <= (s.get("line") or 0) <= patch.start_line + 5: # approximate overlap
                        static_pass = False
                        details["static_fail_reason"] = f"Finding {s.get('rule_id')} still detected."
                        break
                        
            for s in new_security:
                if s.get("rule_id") == original_finding.rule_id and s.get("file") == original_finding.file:
                    if patch.start_line <= (s.get("line") or 0) <= patch.start_line + 5:
                        security_pass = False
                        details["security_fail_reason"] = f"Finding {s.get('rule_id')} still detected."
                        break

            if original_finding.category == "Security" and not security_pass:
                return VerificationResult(VerificationStatus.FAIL_SECURITY, True, static_pass, security_pass, None, "Security finding not resolved.", details)
            elif original_finding.category != "Security" and not static_pass:
                return VerificationResult(VerificationStatus.FAIL_STATIC, True, static_pass, security_pass, None, "Static finding not resolved.", details)
            
            # Stage 3: Runtime Test Verification
            test_status, test_out, test_err = discover_and_run_tests(sandbox.sandbox_root)
            
            details["test_stdout"] = test_out
            details["test_stderr"] = test_err
            
            if test_status == "NOT_AVAILABLE":
                return VerificationResult(
                    status=VerificationStatus.NOT_AVAILABLE,
                    parse_result=True,
                    static_result=static_pass,
                    security_result=security_pass,
                    test_result=None,
                    message="Static/security verification passed; runtime test verification unavailable.",
                    details=details
                )
            elif test_status == "PASS":
                return VerificationResult(
                    status=VerificationStatus.PASS,
                    parse_result=True,
                    static_result=static_pass,
                    security_result=security_pass,
                    test_result=True,
                    message="Fix verified by all static, security, and runtime checks.",
                    details=details
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.FAIL_TEST,
                    parse_result=True,
                    static_result=static_pass,
                    security_result=security_pass,
                    test_result=False,
                    message=f"Runtime tests failed: {test_status}",
                    details=details
                )
    except Exception as e:
        return VerificationResult(VerificationStatus.ERROR, False, message=str(e), details={"exception": str(e)})
