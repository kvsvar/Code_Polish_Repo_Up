"""
backend/analysis/external_adapters/codeql.py

Optional external static-analysis adapter for CodeQL.
Native Tree-sitter rules remain the primary analysis engine. CodeQL is an optional layer.
"""
import os
import sys
import json
import logging
import tempfile
import subprocess
import shutil
from typing import List, Dict, Any, Tuple, Optional
from analysis.finding import Finding

log = logging.getLogger(__name__)

def check_codeql_available() -> Tuple[bool, str, List[str], str]:
    """
    Detects whether CodeQL CLI is available.
    Returns: (is_available, version, supported_languages, reason)
    """
    try:
        # Check version
        version_proc = subprocess.run(["codeql", "--version"], capture_output=True, text=True)
        if version_proc.returncode != 0:
            return False, "", [], "CodeQL command returned non-zero status"
            
        version_output = version_proc.stdout.strip()
        version = version_output.splitlines()[0] if version_output else "Unknown version"
        
        # Check supported languages
        lang_proc = subprocess.run(["codeql", "resolve", "languages"], capture_output=True, text=True)
        supported_languages = []
        if lang_proc.returncode == 0:
            for line in lang_proc.stdout.splitlines():
                lang = line.strip()
                if lang:
                    supported_languages.append(lang)
                    
        return True, version, supported_languages, ""
    except FileNotFoundError:
        return False, "", [], "CodeQL CLI not found in PATH"
    except Exception as e:
        return False, "", [], f"Error checking CodeQL: {str(e)}"


def run_codeql_analysis(project_root: str, language: str) -> List[Finding]:
    """
    Creates a database and runs a small set of queries for a supported repository.
    Returns normalized Findings.
    """
    is_available, version, supported, reason = check_codeql_available()
    if not is_available:
        log.info(f"CodeQL unavailable: {reason}")
        return []
        
    # Map our languages to CodeQL languages
    # e.g., TypeScript -> javascript
    lang_map = {
        "python": "python",
        "javascript": "javascript",
        "typescript": "javascript",
        "java": "java",
        "cpp": "cpp"
    }
    
    codeql_lang = lang_map.get(language.lower())
    if not codeql_lang or codeql_lang not in supported:
        log.info(f"Language {language} not supported by installed CodeQL version.")
        return []
        
    temp_dir = tempfile.mkdtemp(prefix="repo-up-codeql-")
    db_path = os.path.join(temp_dir, "db")
    sarif_path = os.path.join(temp_dir, "results.sarif")
    
    findings = []
    
    try:
        # 1. Database Creation
        db_cmd = [
            "codeql", "database", "create", db_path,
            "--language=" + codeql_lang,
            "--source-root=" + os.path.abspath(project_root)
        ]
        db_proc = subprocess.run(db_cmd, capture_output=True, text=True)
        if db_proc.returncode != 0:
            log.warning("CodeQL database creation failed. Skipping CodeQL analysis.")
            return []
            
        # 2. Query Execution
        # We use a controlled small set of security queries: the security-extended suite.
        query_suite = f"{codeql_lang}-security-extended.qls"
        analyze_cmd = [
            "codeql", "database", "analyze", db_path,
            query_suite,
            "--format=sarif-latest",
            "--output=" + sarif_path
        ]
        
        analyze_proc = subprocess.run(analyze_cmd, capture_output=True, text=True)
        if analyze_proc.returncode != 0:
            log.warning("CodeQL analysis failed. Skipping CodeQL analysis.")
            return []
            
        # 3. Parse SARIF
        if os.path.exists(sarif_path):
            with open(sarif_path, "r", encoding="utf-8") as f:
                sarif_data = json.load(f)
                findings = _parse_sarif(sarif_data, language)
                
    except Exception as e:
        log.error(f"Error during CodeQL execution: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    return findings


def _parse_sarif(sarif_data: Dict[str, Any], language: str) -> List[Finding]:
    """
    Normalizes CodeQL SARIF output into Repo-Up Findings.
    """
    findings = []
    runs = sarif_data.get("runs", [])
    if not runs:
        return findings
        
    for run in runs:
        # We can extract rule metadata from tool.driver.rules if we need severity/CWE
        rules_meta = {}
        tool = run.get("tool", {}).get("driver", {})
        for rule in tool.get("rules", []):
            rule_id = rule.get("id", "")
            tags = rule.get("properties", {}).get("tags", [])
            # Try to find CWE in tags
            cwe = None
            for tag in tags:
                if str(tag).upper().startswith("CWE-"):
                    cwe = tag.upper()
                    break
                    
            rules_meta[rule_id] = {
                "cwe": cwe,
                "name": rule.get("name", rule_id),
                "severity": rule.get("properties", {}).get("problem.severity", "warning")
            }
            
        results = run.get("results", [])
        for result in results:
            rule_id = result.get("ruleId", "UNKNOWN")
            message = result.get("message", {}).get("text", "CodeQL finding")
            
            locations = result.get("locations", [])
            file_path = None
            line = None
            column = None
            
            if locations:
                phys = locations[0].get("physicalLocation", {})
                art = phys.get("artifactLocation", {})
                file_path = art.get("uri")
                reg = phys.get("region", {})
                line = reg.get("startLine")
                column = reg.get("startColumn")
                
            meta = rules_meta.get(rule_id, {})
            cwe = meta.get("cwe")
            raw_severity = meta.get("severity", "warning").lower()
            
            if raw_severity == "error":
                severity = "High"
            elif raw_severity == "warning":
                severity = "Medium"
            else:
                severity = "Low"
                
            finding = Finding(
                rule_id=f"CODEQL-{rule_id.upper()}",
                category="Security",
                title=f"CodeQL: {meta.get('name', rule_id)}",
                description=message,
                severity=severity,
                rule=rule_id,
                language=language,
                file=file_path,
                line=line,
                column=column,
                cwe=cwe,
                source="CodeQL"
            )
            findings.append(finding)
            
    return findings
