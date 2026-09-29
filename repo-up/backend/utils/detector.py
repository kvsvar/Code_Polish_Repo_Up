import os
import json

def detect_project_details(session_dir: str):
    file_count = 0
    folder_count = 0
    languages = set()
    frameworks = set()

    for root, dirs, files in os.walk(session_dir):
        # Exclude common large directories from detailed scanning but count them
        is_ignored_dir = any(ignored in root for ignored in ['node_modules', 'venv', '.venv', '.git', '__pycache__'])
        
        if not is_ignored_dir:
            folder_count += len(dirs)
            file_count += len(files)
            
            # Language detection
            if "requirements.txt" in files or "pyproject.toml" in files:
                languages.add("Python")
            if "package.json" in files:
                languages.add("JavaScript")
            if "tsconfig.json" in files:
                languages.add("TypeScript")

            # Framework detection - Node.js
            if "package.json" in files:
                try:
                    with open(os.path.join(root, "package.json"), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        deps = data.get("dependencies", {})
                        dev_deps = data.get("devDependencies", {})
                        all_deps = {**deps, **dev_deps}

                        if "next" in all_deps:
                            frameworks.add("Next.js")
                        elif "react" in all_deps:
                            frameworks.add("React")
                        
                        if "express" in all_deps:
                            frameworks.add("Express")
                        
                        if "@nestjs/core" in all_deps or "@nestjs/common" in all_deps:
                            frameworks.add("NestJS")
                except Exception:
                    pass

            # Framework detection - Python
            for file in files:
                if file == "manage.py":
                    frameworks.add("Django")
                    
                if file.endswith(".py"):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            content = f.read()
                            if "from flask import" in content or "import flask" in content:
                                frameworks.add("Flask")
                            if "from fastapi import" in content or "import fastapi" in content:
                                frameworks.add("FastAPI")
                            if "django" in content and "import" in content:
                                frameworks.add("Django")
                    except Exception:
                        pass
        else:
            # We still want to count files/folders in ignored dirs
            folder_count += len(dirs)
            file_count += len(files)

    return file_count, folder_count, list(languages), list(frameworks)
