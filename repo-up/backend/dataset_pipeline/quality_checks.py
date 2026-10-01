from typing import List
from .schema import DatasetRecord

def check_dataset_quality(records: List[DatasetRecord]) -> List[str]:
    """
    Validates dataset quality. Returns a list of errors.
    Checks for: duplicate records, missing provenance, invalid hashes, 
    missing language, missing rule, inconsistent verification status.
    """
    errors = []
    seen_hashes = set()
    
    for idx, r in enumerate(records):
        record_id = f"Record {idx} ({r.repository_id}:{r.file}:{r.rule})"
        
        dup_key = (r.repository_id, r.file, r.rule, r.original_code_hash)
        if dup_key in seen_hashes:
            errors.append(f"{record_id}: Duplicate record found.")
        seen_hashes.add(dup_key)
        
        if not r.language or r.language == "Unknown":
            errors.append(f"{record_id}: Missing language.")
            
        if not r.rule:
            errors.append(f"{record_id}: Missing rule.")
            
        if not r.original_code_hash:
            errors.append(f"{record_id}: Missing original_code_hash provenance.")
            
        if r.final_status in ("STATIC_VERIFIED", "FULLY_VERIFIED", "REPAIRED_UNVERIFIED"):
            if not r.patched_code_hash:
                errors.append(f"{record_id}: Status {r.final_status} but missing patched_code_hash.")
            if not r.candidate_patch:
                errors.append(f"{record_id}: Status {r.final_status} but missing candidate_patch.")
                
        if r.final_status == "FULLY_VERIFIED" and not r.test_verification:
            errors.append(f"{record_id}: Status is FULLY_VERIFIED but test_verification is not True.")
            
        if r.final_status == "STATIC_VERIFIED" and not r.static_verification and not r.security_verification:
            errors.append(f"{record_id}: Status is STATIC_VERIFIED but static/security verifications are False/None.")
            
    return errors
