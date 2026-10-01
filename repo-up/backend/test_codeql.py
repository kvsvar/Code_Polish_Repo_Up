"""
backend/test_codeql.py

Tests for the CodeQL External Static Security Assessment Adapter.
"""
import unittest
from unittest.mock import patch, MagicMock
from analysis.external_adapters.codeql import check_codeql_available, run_codeql_analysis

class TestCodeQLAdapter(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_codeql_absent(self, mock_run):
        # Simulate CodeQL not in PATH
        mock_run.side_effect = FileNotFoundError("No such file or directory")
        is_avail, ver, langs, reason = check_codeql_available()
        self.assertFalse(is_avail)
        self.assertIn("not found", reason)
        
        # Test analysis skips gracefully
        findings = run_codeql_analysis(".", "python")
        self.assertEqual(len(findings), 0)

    @patch('subprocess.run')
    def test_codeql_available_clean(self, mock_run):
        # Setup mock for version and languages
        def side_effect(args, **kwargs):
            mock = MagicMock()
            mock.returncode = 0
            if "--version" in args:
                mock.stdout = "CodeQL command-line toolchain release 2.14.0"
            elif "resolve" in args and "languages" in args:
                mock.stdout = "python\njavascript\ncpp\n"
            elif "database" in args and "create" in args:
                mock.stdout = "Successfully created database"
            elif "database" in args and "analyze" in args:
                mock.stdout = "Analysis complete"
                # We need to simulate the sarif output creation, but we can mock json.load or open
            return mock
            
        mock_run.side_effect = side_effect
        
        is_avail, ver, langs, reason = check_codeql_available()
        self.assertTrue(is_avail)
        self.assertEqual(ver, "CodeQL command-line toolchain release 2.14.0")
        self.assertIn("python", langs)
        
        # Simulate empty SARIF results
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data='{"runs": []}')):
                findings = run_codeql_analysis(".", "python")
                self.assertEqual(len(findings), 0)

    @patch('subprocess.run')
    def test_codeql_available_vulnerable(self, mock_run):
        def side_effect(args, **kwargs):
            mock = MagicMock()
            mock.returncode = 0
            if "--version" in args:
                mock.stdout = "CodeQL command-line toolchain release 2.14.0"
            elif "resolve" in args and "languages" in args:
                mock.stdout = "python\n"
            return mock
            
        mock_run.side_effect = side_effect
        
        vuln_sarif = '''
        {
          "runs": [
            {
              "tool": {
                "driver": {
                  "rules": [
                    {
                      "id": "py/hardcoded-credentials",
                      "name": "Hard-coded credentials",
                      "properties": {
                        "tags": ["CWE-798"],
                        "problem.severity": "error"
                      }
                    }
                  ]
                }
              },
              "results": [
                {
                  "ruleId": "py/hardcoded-credentials",
                  "message": { "text": "Hard-coded credential detected." },
                  "locations": [
                    {
                      "physicalLocation": {
                        "artifactLocation": { "uri": "main.py" },
                        "region": { "startLine": 10 }
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
        '''
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data=vuln_sarif)):
                findings = run_codeql_analysis(".", "python")
                self.assertEqual(len(findings), 1)
                f = findings[0]
                self.assertEqual(f.rule_id, "CODEQL-PY/HARDCODED-CREDENTIALS")
                self.assertEqual(f.cwe, "CWE-798")
                self.assertEqual(f.severity, "High")
                self.assertEqual(f.source, "CodeQL")
                self.assertEqual(f.file, "main.py")
                self.assertEqual(f.line, 10)

    @patch('subprocess.run')
    def test_codeql_malformed_repo(self, mock_run):
        # Database creation fails
        def side_effect(args, **kwargs):
            mock = MagicMock()
            if "--version" in args:
                mock.returncode = 0
                mock.stdout = "CodeQL CLI"
            elif "resolve" in args and "languages" in args:
                mock.returncode = 0
                mock.stdout = "python\n"
            elif "database" in args and "create" in args:
                mock.returncode = 1 # Fails
                mock.stdout = "Error building database"
            return mock
            
        mock_run.side_effect = side_effect
        
        findings = run_codeql_analysis(".", "python")
        self.assertEqual(len(findings), 0)

if __name__ == "__main__":
    unittest.main()
