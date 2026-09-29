import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.rules.structural import run_structural_rules
from analysis.rules.security import run_security_rules
from analysis.rules.ast_security import run_ast_security_rules
from services.graph_service import build_dependency_graph
from analysis.metrics.graph_metrics import cof, afferent_couplings
from analysis.metrics.class_metrics import calculate_repo_averages
from analysis.scorer import compute_repo_score

def analyze_mock_repo(path: str):
    findings, struct_score = run_structural_rules(path)
    
    sec_findings_1, sec_penalty_1 = run_security_rules(path)
    sec_findings_2, sec_penalty_2 = run_ast_security_rules(path)
    security_score = max(0, 100 - (sec_penalty_1 + sec_penalty_2))
    graph = build_dependency_graph(path)
    sys_cof = cof(graph)
    if graph.number_of_nodes() > 0:
        avg_afferent = sum(afferent_couplings(graph, n) for n in graph.nodes()) / graph.number_of_nodes()
    else:
        avg_afferent = 0.0
    class_avgs, metric_findings = calculate_repo_averages(path)
    
    repo_metrics = {
        "cof": sys_cof,
        "avg_afferent": avg_afferent,
        "avg_public_fields": class_avgs["avg_public_fields"],
        "avg_public_methods": class_avgs["avg_public_methods"],
        "avg_dit": class_avgs["avg_dit"],
        "avg_lcom": class_avgs["avg_lcom"]
    }
    
    return compute_repo_score(repo_metrics, struct_score, security_score)

def create_good_repo(base: str):
    os.makedirs(os.path.join(base, "src"))
    os.makedirs(os.path.join(base, "tests"))
    
    with open(os.path.join(base, "requirements.txt"), "w") as f:
        f.write("fastapi\n")
    with open(os.path.join(base, "README.md"), "w") as f:
        f.write("# Good Repo\n")
    with open(os.path.join(base, ".env.example"), "w") as f:
        f.write("ENV=dev\n")
        
    with open(os.path.join(base, "src", "models.py"), "w") as f:
        f.write('class User:\n    def __init__(self):\n        self.id = 1\n    def get_id(self):\n        return self.id\n')
    with open(os.path.join(base, "src", "service.py"), "w") as f:
        f.write('from src.models import User\nclass UserService:\n    def __init__(self):\n        self.user = User()\n    def get_user(self):\n        return self.user.get_id()\n')
        
def create_bad_repo(base: str):
    with open(os.path.join(base, "god_class.py"), "w") as f:
        methods = "\n".join([f"    def m{i}(self): pass" for i in range(1, 45)])
        f.write(f'class Base1: pass\nclass GodClass(Base1):\n{methods}\n')

def main():
    test_dir = os.path.join(os.path.dirname(__file__), "temp_validation")
    good_dir = os.path.join(test_dir, "good")
    bad_dir = os.path.join(test_dir, "bad")
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(good_dir)
    os.makedirs(bad_dir)
    
    create_good_repo(good_dir)
    create_bad_repo(bad_dir)
    
    good_score = analyze_mock_repo(good_dir)
    bad_score = analyze_mock_repo(bad_dir)
    
    print("--- GOOD REPO ---")
    import json
    print(json.dumps(good_score, indent=2))
    
    print("\\n--- BAD REPO ---")
    print(json.dumps(bad_score, indent=2))
    
    diff = good_score["final_score"] - bad_score["final_score"]
    print(f"\\nScore Difference: {diff:.1f} points")
    
    if diff >= 20:
        print("Validation PASSED: Scorer differentiates Good vs Bad by 20+ points.")
    else:
        print("Validation FAILED: Difference is too small.")

if __name__ == "__main__":
    main()
