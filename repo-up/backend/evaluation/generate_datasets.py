import os
import json

BASE_DIR = os.path.join(os.path.dirname(__file__), "datasets")

DATA = {
    "python": {
        "ext": "py",
        "clean": "def hello():\n    print('hello world')\n",
        "code_smells": "a = 1\nb = 1\na = 1\n# " + "A" * 120 + "\n", # Duplicate + long line
        "security": "import subprocess\nsubprocess.call(user_input, shell=True)\n",
        "structural": "from .a import *\n",
        "mixed": "import md5\nh = md5.new()\n# " + "X" * 120 + "\n"
    },
    "javascript": {
        "ext": "js",
        "clean": "function hello() { console.log('hello'); }\n",
        "code_smells": "var a = 1; var b = 1; var a = 1;\n// " + "A" * 120 + "\n",
        "security": "eval('console.log(user_input)');\n",
        "structural": "require('./a');\n",
        "mixed": "var crypto = require('crypto');\ncrypto.createHash('md5');\n// " + "X" * 120 + "\n"
    },
    "typescript": {
        "ext": "ts",
        "clean": "function hello(): void { console.log('hello'); }\n",
        "code_smells": "let a: number = 1; let a: number = 1;\n// " + "A" * 120 + "\n",
        "security": "eval('console.log(user_input)');\n",
        "structural": "import {a} from './a';\n",
        "mixed": "const crypto = require('crypto');\ncrypto.createHash('md5');\n// " + "X" * 120 + "\n"
    },
    "java": {
        "ext": "java",
        "clean": "class Hello { void say() { System.out.println(\"Hi\"); } }\n",
        "code_smells": "class A {\n// " + "A" * 120 + "\n}\n",
        "security": "Runtime.getRuntime().exec(userInput);\n",
        "structural": "import a.b.c;\n",
        "mixed": "MessageDigest md = MessageDigest.getInstance(\"MD5\");\n// " + "X" * 120 + "\n"
    },
    "cpp": {
        "ext": "cpp",
        "clean": "void hello() { }\n",
        "code_smells": "int a = 1;\n// " + "A" * 120 + "\n",
        "security": "system(userInput);\n",
        "structural": "#include \"a.h\"\n",
        "mixed": "MD5(input);\n// " + "X" * 120 + "\n"
    }
}

MANIFEST_EXPECTATIONS = {
    "clean": [],
    "code_smells": [
        {"rule": "CODE-LONG-LINE", "line": 4, "severity": "Low"}
    ],
    "security": [
        {"rule": "SEC-EVAL-EXEC", "line": 2, "severity": "High"}
    ],
    "structural": [
    ],
    "mixed": [
        {"rule": "SEC-WEAK-CRYPTO", "line": 2, "severity": "Medium"},
        {"rule": "CODE-LONG-LINE", "line": 3, "severity": "Low"}
    ]
}

def generate():
    for lang, info in DATA.items():
        ext = info["ext"]
        for cat in ["clean", "code_smells", "security", "structural", "mixed"]:
            cat_dir = os.path.join(BASE_DIR, lang, cat)
            os.makedirs(cat_dir, exist_ok=True)
            
            # Write source code
            file_name = f"main.{ext}"
            file_path = os.path.join(cat_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(info[cat])
                
            # Write manifest
            expected = []
            for ex in MANIFEST_EXPECTATIONS[cat]:
                expected.append({
                    "rule": ex["rule"],
                    "file": file_name,
                    "line": ex["line"],
                    "severity": ex["severity"]
                })
                
            # Customize rules for specific languages / cases to be realistic
            if cat == "code_smells":
                if lang == "java":
                    expected = [{"rule": "CODE-LONG-LINE", "file": file_name, "line": 2, "severity": "Low"}]
                elif lang == "cpp":
                    expected = [{"rule": "CODE-LONG-LINE", "file": file_name, "line": 2, "severity": "Low"}]
            elif cat == "security":
                if lang == "python":
                    expected = [{"rule": "SEC-EVAL-EXEC", "file": file_name, "line": 2, "severity": "High"}]
                elif lang in ("javascript", "typescript"):
                    expected = [{"rule": "SEC-EVAL-EXEC", "file": file_name, "line": 1, "severity": "High"}]
                elif lang == "java":
                    expected = [{"rule": "SEC-EVAL-EXEC", "file": file_name, "line": 1, "severity": "High"}]
                elif lang == "cpp":
                    expected = [{"rule": "SEC-EVAL-EXEC", "file": file_name, "line": 1, "severity": "High"}]
            elif cat == "mixed":
                if lang == "python":
                    expected[0]["line"] = 2
                    expected[1]["line"] = 3
                elif lang in ("javascript", "typescript"):
                    expected[0]["line"] = 2
                    expected[1]["line"] = 3
                elif lang == "java":
                    expected[0]["line"] = 1
                    expected[1]["line"] = 2
                elif lang == "cpp":
                    expected[0]["line"] = 1
                    expected[1]["line"] = 2

            manifest = {
                "repository": f"{lang}_{cat}",
                "language": lang,
                "dataset_version": "1.0",
                "expected_findings": expected
            }
            
            with open(os.path.join(cat_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    generate()
    print("Datasets generated.")
