import unittest
import os
from analysis.finding import Finding
from verification.result import VerificationResult, VerificationStatus
from dataset_pipeline.pipeline import process_finding
from dataset_pipeline.quality_checks import check_dataset_quality
from dataset_pipeline.schema import DatasetRecord
from dataset_pipeline.exporter import export_jsonl, export_csv_summary, export_markdown_stats

class TestDatasetPipeline(unittest.TestCase):
    def setUp(self):
        self.finding = Finding("SEC-CWE-79", "Sec", "XSS", "desc", "High", language="python", file="app.py")
        self.original_code = "print(user_input)"
        self.patched_code = "import html\nprint(html.escape(user_input))"
        self.patch = "@@ -1 +1,2 @@\n+import html\n-print(user_input)\n+print(html.escape(user_input))"
        
    def test_vulnerable_record(self):
        record = process_finding("repo_1", self.finding, self.original_code)
        self.assertEqual(record.final_status, "VULNERABLE")
        self.assertEqual(record.original_code_hash, DatasetRecord.hash_content(self.original_code))
        self.assertIsNone(record.patched_code_hash)
        
        errors = check_dataset_quality([record])
        self.assertEqual(len(errors), 0)
        
    def test_static_verified_record(self):
        verif = VerificationResult(status=VerificationStatus.PASS, parse_result=True, static_result=True)
        record = process_finding("repo_1", self.finding, self.original_code, self.patch, self.patched_code, verif)
        
        self.assertEqual(record.final_status, "STATIC_VERIFIED")
        self.assertEqual(record.patched_code_hash, DatasetRecord.hash_content(self.patched_code))
        
        errors = check_dataset_quality([record])
        self.assertEqual(len(errors), 0)
        
    def test_fully_verified_record(self):
        verif = VerificationResult(status=VerificationStatus.PASS, parse_result=True, static_result=True, test_result=True)
        record = process_finding("repo_1", self.finding, self.original_code, self.patch, self.patched_code, verif)
        
        self.assertEqual(record.final_status, "FULLY_VERIFIED")
        
        errors = check_dataset_quality([record])
        self.assertEqual(len(errors), 0)
        
    def test_failed_verification_record(self):
        verif = VerificationResult(status=VerificationStatus.FAIL_STATIC, parse_result=True, static_result=False)
        record = process_finding("repo_1", self.finding, self.original_code, self.patch, self.patched_code, verif)
        
        self.assertEqual(record.final_status, "FAILED_VERIFICATION")
        
        errors = check_dataset_quality([record])
        self.assertEqual(len(errors), 0)
        
    def test_quality_checks(self):
        record = process_finding("repo_1", self.finding, self.original_code)
        record.language = None
        errors = check_dataset_quality([record, record]) # Also duplicate
        self.assertTrue(any("Duplicate" in e for e in errors))
        self.assertTrue(any("Missing language" in e for e in errors))

    def test_exporters(self):
        verif = VerificationResult(status=VerificationStatus.PASS, parse_result=True, static_result=True, test_result=True)
        record = process_finding("repo_1", self.finding, self.original_code, self.patch, self.patched_code, verif)
        
        export_jsonl([record], "test.jsonl")
        export_csv_summary([record], "test.csv")
        export_markdown_stats([record], "test.md")
        
        self.assertTrue(os.path.exists("test.jsonl"))
        self.assertTrue(os.path.exists("test.csv"))
        self.assertTrue(os.path.exists("test.md"))
        
        os.remove("test.jsonl")
        os.remove("test.csv")
        os.remove("test.md")

if __name__ == "__main__":
    unittest.main()
