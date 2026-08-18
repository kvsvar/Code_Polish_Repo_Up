import os
import shutil
import zipfile

def generate_bad_repo():
    repo_name = "test_repo_bad"
    if os.path.exists(repo_name):
        shutil.rmtree(repo_name)
    os.makedirs(repo_name)

    files_generated = []

    # 1. God Classes (High LCOM, High Public Surface)
    for i in range(1, 4): # 3 God Classes
        class_name = f"GodClass{i}"
        filename = f"{class_name}.py"
        filepath = os.path.join(repo_name, filename)
        
        lines = []
        lines.append(f"import HubCore\n")
        lines.append(f"class {class_name}:\n")
        lines.append(f"    def __init__(self):\n")
        for f in range(1, 31):
            lines.append(f"        self.public_field_{f} = {f}\n")
        
        for m in range(1, 31):
            lines.append(f"\n    def do_action_with_field_{m}(self):\n")
            lines.append(f"        # Completely isolated method, driving LCOM up\n")
            lines.append(f"        return self.public_field_{m} * 10\n")
            
        with open(filepath, "w") as f:
            f.writelines(lines)
        files_generated.append(filename)

    # 2. Inheritance Chain (High DIT)
    chain_levels = 6
    for i in range(1, chain_levels + 1):
        class_name = f"ChainLevel{i}"
        filename = f"{class_name}.py"
        filepath = os.path.join(repo_name, filename)
        
        lines = ["import HubCore\n"]
        if i > 1:
            lines.append(f"from ChainLevel{i-1} import ChainLevel{i-1}\n")
            lines.append(f"class {class_name}(ChainLevel{i-1}):\n")
        else:
            lines.append(f"class {class_name}:\n")
            
        lines.append(f"    def __init__(self):\n")
        if i > 1:
            lines.append(f"        super().__init__()\n")
        lines.append(f"        self.level_{i}_field = 'level {i}'\n\n")
        
        lines.append(f"    def method_level_{i}(self):\n")
        lines.append(f"        return self.level_{i}_field\n")
        
        with open(filepath, "w") as f:
            f.writelines(lines)
        files_generated.append(filename)

    # 3. Duplicated Logic
    duplicate_code = """
    def calculate_complex_business_logic(data):
        result = 0
        for item in data:
            if item > 10:
                result += item * 2
            elif item < 5:
                result -= item
            else:
                result += 1
        return result
    """
    for i in range(1, 5): # 4 duplicated files
        filename = f"DuplicatedLogic{i}.py"
        filepath = os.path.join(repo_name, filename)
        lines = ["import HubCore\n"]
        lines.append(duplicate_code.replace("calculate_complex_business_logic", f"calculate_logic_variant_{i}").replace("data", "input_array"))
        
        with open(filepath, "w") as f:
            f.writelines(lines)
        files_generated.append(filename)

    # 4. Filler files to bump file count
    for i in range(1, 10):
        filename = f"FillerUtility{i}.py"
        filepath = os.path.join(repo_name, filename)
        lines = ["import HubCore\n\n"]
        lines.append(f"class Filler{i}:\n")
        lines.append(f"    def util_method(self):\n")
        lines.append(f"        pass\n")
        with open(filepath, "w") as f:
            f.writelines(lines)
        files_generated.append(filename)

    # 5. HubCore (High Coupling)
    # It imports EVERY other file, and every other file imported it!
    hub_filename = "HubCore.py"
    hub_filepath = os.path.join(repo_name, hub_filename)
    hub_lines = []
    for f in files_generated:
        module_name = f.replace(".py", "")
        hub_lines.append(f"import {module_name}\n")
    
    hub_lines.append("\nclass GodHubController:\n")
    hub_lines.append("    def orchestrate_everything(self):\n")
    hub_lines.append("        pass\n")
    
    with open(hub_filepath, "w") as f:
        f.writelines(hub_lines)
    files_generated.append(hub_filename)

    # Zip it up
    zip_filename = f"{repo_name}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(repo_name):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=os.path.relpath(file_path, repo_name))

    print("=== SYNTHETIC BAD REPO GENERATED ===")
    print(f"Zip created: {zip_filename}")
    print(f"Total Files: {len(files_generated)}")
    print(f"Directory Structure: FLAT (No src/, no tests/)")
    print(f"Manifests: MISSING (No README, requirements.txt, etc.)")
    print("\nEXPECTED METRICS:")
    print("- LCOM: > 0.9 on GodClasses (30 isolated methods/fields each)")
    print("- DIT: 6 (ChainLevel6 inherits through 5 parents)")
    print("- Coupling: Extreme (HubCore imports ~21 files, and all 21 import HubCore creating circular tangles)")
    print("- Encapsulation: Poor (100% public fields/methods)")
    print("- Duplication: 4 near-identical functions")

    # Clean up directory
    shutil.rmtree(repo_name, ignore_errors=True)

if __name__ == "__main__":
    generate_bad_repo()
