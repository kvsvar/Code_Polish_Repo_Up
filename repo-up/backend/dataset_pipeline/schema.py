import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class DatasetRecord:
    repository_id: str
    language: str
    file: str
    rule: str
    cwe: Optional[str]
    original_code_hash: str
    original_finding: Dict[str, Any]
    candidate_patch: Optional[str] = None
    patched_code_hash: Optional[str] = None
    static_verification: Optional[bool] = None
    security_verification: Optional[bool] = None
    test_verification: Optional[bool] = None
    final_status: str = "VULNERABLE"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tool_version: str = "1.0"
    
    def to_dict(self):
        return asdict(self)
        
    @staticmethod
    def hash_content(content: str) -> str:
        if not content:
            return ""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
