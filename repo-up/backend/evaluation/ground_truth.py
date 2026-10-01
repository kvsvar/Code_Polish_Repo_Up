from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ExpectedFinding:
    rule: str
    file: str
    line: Optional[int] = None
    severity: Optional[str] = None
    cwe: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BenchmarkManifest:
    repository: str
    language: str
    dataset_version: str = "1.0"
    expected_findings: List[ExpectedFinding] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "BenchmarkManifest":
        findings = [
            ExpectedFinding(
                rule=f.get("rule", ""),
                file=f.get("file", ""),
                line=f.get("line"),
                severity=f.get("severity"),
                cwe=f.get("cwe"),
                metadata=f.get("metadata", {})
            )
            for f in data.get("expected_findings", [])
        ]
        return cls(
            repository=data.get("repository", "unknown"),
            language=data.get("language", "unknown"),
            dataset_version=data.get("dataset_version", "1.0"),
            expected_findings=findings
        )
