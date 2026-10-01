import unittest
from analysis.finding import Finding
from evaluation.ground_truth import BenchmarkManifest, ExpectedFinding
from evaluation.matching import compute_matches
from evaluation.metrics import calculate_metrics, calculate_pass_at_k
from evaluation.report import generate_evaluation_report

class TestEvaluationFramework(unittest.TestCase):
    def test_matching_logic_exact(self):
        expected = ExpectedFinding(rule="SEC-CWE-502", file="src/main.py", line=10)
        actual = Finding(rule_id="SEC-CWE-502", category="Sec", title="", description="", severity="High", file="src/main.py", line=10)
        
        matched, fp, fn = compute_matches([expected], [actual])
        self.assertEqual(len(matched), 1)
        self.assertEqual(len(fp), 0)
        self.assertEqual(len(fn), 0)

    def test_matching_logic_tolerance(self):
        expected = ExpectedFinding(rule="SEC-CWE-502", file="src/main.py", line=10)
        actual = Finding(rule_id="SEC-CWE-502", category="Sec", title="", description="", severity="High", file="src/main.py", line=12)
        
        matched, fp, fn = compute_matches([expected], [actual], line_tolerance=3)
        self.assertEqual(len(matched), 1)

        matched, fp, fn = compute_matches([expected], [actual], line_tolerance=1)
        self.assertEqual(len(matched), 0)
        self.assertEqual(len(fp), 1)
        self.assertEqual(len(fn), 1)

    def test_metrics_calculation(self):
        res = calculate_metrics(tp=5, fp=2, fn=3)
        self.assertEqual(res["precision"], 5/7)
        self.assertEqual(res["recall"], 5/8)
        
        # pass@k
        # n=10, c=2, k=1 -> pass@1 = 2/10 = 0.2
        self.assertAlmostEqual(calculate_pass_at_k(1, 2, 10), 0.2)
        
        # n=10, c=1, k=10 -> pass@10 = 1.0
        self.assertEqual(calculate_pass_at_k(10, 1, 10), 1.0)
        
        # n=10, c=0, k=5 -> pass@5 = 0.0
        self.assertEqual(calculate_pass_at_k(5, 0, 10), 0.0)

    def test_report_generation(self):
        manifest = BenchmarkManifest("repo_a", "Python", "1.0", [
            ExpectedFinding("SEC-CWE-502", "main.py", 10),
            ExpectedFinding("CODE-LONG-LINE", "utils.py", 5)
        ])
        
        matched = [manifest.expected_findings[0]]
        fp = [Finding("STRUCT-BAD", "Struct", "", "", "High", file="main.py", line=2)]
        fn = [manifest.expected_findings[1]]
        
        report = generate_evaluation_report(manifest, matched, fp, fn)
        
        self.assertEqual(report["overall_metrics"]["tp"], 1)
        self.assertEqual(report["overall_metrics"]["fp"], 1)
        self.assertEqual(report["overall_metrics"]["fn"], 1)
        
        # Category checks
        self.assertEqual(report["category_metrics"]["Security"]["tp"], 1)
        self.assertEqual(report["category_metrics"]["Structural"]["fp"], 1)
        self.assertEqual(report["category_metrics"]["Code Smell"]["fn"], 1)

if __name__ == "__main__":
    unittest.main()
