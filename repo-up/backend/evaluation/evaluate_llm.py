import os
import json
from typing import List, Dict, Any
from analysis.finding import Finding
from verification.runner import verify_patch
from llm.llm_engine import explain_and_suggest_patch
from evaluation.metrics import calculate_pass_at_k, calculate_secure_at_k, calculate_vulnerable_at_k
from llm.provider import LLMProvider
import llm.llm_engine

class MockLLMProvider(LLMProvider):
    def generate_explanation(self, context: dict) -> str:
        return "Test AI Explanation."
        
    def generate_patch(self, context: dict) -> Dict[str, Any]:
        # Return a valid patch that replaces one line with another
        return {
            "file": context.get("file", "test.py"),
            "old_text": "print(user_input)\n",
            "new_text": "import html\nprint(html.escape(user_input))\n",
            "reason": "Fix XSS"
        }

def evaluate_llm_patches(findings: List[Dict[str, Any]], project_root: str, k: int = 3):
    """
    Feeds LLM candidate patches into the evaluation subsystem.
    Records count of candidates, valid patches, static passes, etc.
    Calculates pass@k.
    """
    # Inject Mock Provider for Evaluation purposes
    llm.llm_engine.get_provider = lambda: MockLLMProvider()
    
    stats = {
        "candidate_count": 0,
        "valid_patch_count": 0,
        "static_pass_count": 0,
        "security_pass_count": 0,
        "test_pass_count": 0
    }
    
    for finding_dict in findings:
        for _ in range(k):
            stats["candidate_count"] += 1
            
            explanation, patch_obj = explain_and_suggest_patch(finding_dict, project_root)
            if patch_obj:
                stats["valid_patch_count"] += 1
                finding = Finding.from_dict(finding_dict)
                ver_result = verify_patch(project_root, patch_obj, finding)
                
                if ver_result.static_result or ver_result.parse_result:
                    stats["static_pass_count"] += 1
                if ver_result.security_result:
                    stats["security_pass_count"] += 1
                if ver_result.test_result:
                    stats["test_pass_count"] += 1
                    
    # Calculate paper metrics assuming total 'n' generated is candidate_count
    # and 'c' correct is static_pass_count for pass@k.
    pass_at_k = calculate_pass_at_k(k, stats["static_pass_count"], stats["candidate_count"])
    secure_at_k = calculate_secure_at_k(k, stats["security_pass_count"], stats["candidate_count"])
    
    return {
        "stats": stats,
        "pass_at_k": pass_at_k,
        "secure_at_k": secure_at_k
    }

if __name__ == "__main__":
    # Small test wrapper
    finding = {
        "rule_id": "SEC-CWE-79",
        "language": "python",
        "file": "test.py",
        "line": 1,
        "description": "XSS"
    }
    
    # Create dummy project for test
    os.makedirs("test_eval_llm", exist_ok=True)
    with open("test_eval_llm/test.py", "w") as f:
        f.write("print(user_input)\n")
        
    try:
        results = evaluate_llm_patches([finding], "test_eval_llm", k=3)
        print("LLM Evaluation Results:")
        print(json.dumps(results, indent=2))
    finally:
        os.remove("test_eval_llm/test.py")
        os.rmdir("test_eval_llm")
