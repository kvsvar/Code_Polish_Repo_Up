import os
import json
from typing import Dict, Any, Optional
from analysis.finding import Finding
from verification.result import VerificationResult, VerificationStatus
from .schema import DatasetRecord

def process_finding(
    repository_id: str,
    finding: Finding,
    original_code: str,
    candidate_patch: Optional[str] = None,
    patched_code: Optional[str] = None,
    verification: Optional[VerificationResult] = None
) -> DatasetRecord:
    """
    Processes a finding, optional patch, and optional verification into a DatasetRecord.
    Classifies the final status appropriately based on Phase-6 verification policy.
    """
    status = "VULNERABLE"
    
    if candidate_patch and patched_code:
        status = "REPAIRED_UNVERIFIED"
        
    if verification:
        if verification.status != VerificationStatus.PASS:
            status = "FAILED_VERIFICATION"
        else:
            if verification.test_result:
                status = "FULLY_VERIFIED"
            elif verification.static_result or verification.security_result:
                status = "STATIC_VERIFIED"
                
    record = DatasetRecord(
        repository_id=repository_id,
        language=finding.language or "Unknown",
        file=finding.file or "Unknown",
        rule=finding.rule_id,
        cwe=finding.cwe,
        original_code_hash=DatasetRecord.hash_content(original_code),
        original_finding=finding.to_dict(),
        candidate_patch=candidate_patch,
        patched_code_hash=DatasetRecord.hash_content(patched_code) if patched_code else None,
        static_verification=verification.static_result if verification else None,
        security_verification=verification.security_result if verification else None,
        test_verification=verification.test_result if verification else None,
        final_status=status
    )
    
    return record
