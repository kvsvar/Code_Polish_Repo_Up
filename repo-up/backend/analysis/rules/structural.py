import os

# Define configurable rules
# Each rule has a check function that takes (files, dirs) from the project root
STRUCTURAL_RULES = [
    {
        "id": "missing_readme",
        "check": lambda files, dirs: not any(f.lower() == "readme.md" for f in files),
        "penalty": 15,
        "finding": {
            "title": "Missing README",
            "description": "Project has no documentation.",
            "severity": "High"
        }
    },
    {
        "id": "missing_src",
        "check": lambda files, dirs: "src" not in dirs,
        "penalty": 10,
        "finding": {
            "title": "No src folder",
            "description": "Source files are placed in root.",
            "severity": "Medium"
        }
    },
    {
        "id": "missing_tests",
        "check": lambda files, dirs: "tests" not in dirs and "test" not in dirs,
        "penalty": 8,
        "finding": {
            "title": "No tests folder",
            "description": "Project lacks a dedicated tests directory.",
            "severity": "High"
        }
    },
    {
        "id": "missing_dependencies",
        "check": lambda files, dirs: "requirements.txt" not in files and "package.json" not in files,
        "penalty": 10,
        "finding": {
            "title": "Missing dependencies file",
            "description": "Project has neither requirements.txt nor package.json.",
            "severity": "High"
        }
    },
    {
        "id": "missing_env_example",
        "check": lambda files, dirs: ".env.example" not in files,
        "penalty": 5,
        "finding": {
            "title": "Missing .env.example",
            "description": "Project lacks an example environment variables file.",
            "severity": "Medium"
        }
    }
]

def run_structural_rules(project_path: str):
    """
    Evaluates the project against defined structural rules.
    Typically these checks are performed at the root of the project.
    """
    try:
        root_items = os.listdir(project_path)
        files = [f for f in root_items if os.path.isfile(os.path.join(project_path, f))]
        dirs = [d for d in root_items if os.path.isdir(os.path.join(project_path, d))]
    except Exception:
        return [], 100

    findings = []
    score = 100
    for rule in STRUCTURAL_RULES:
        if rule["check"](files, dirs):
            finding = dict(rule["finding"])
            finding["category"] = "Structural"
            findings.append(finding)
            score -= rule.get("penalty", 0)

    score = max(0, score)
    return findings, score
