import os
import shutil
import random
import zipfile

def generate_repo(name: str, size: str):
    num_files = 35 if size == 'medium' else 180
    
    base_dir = os.path.join(os.getcwd(), name)
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir)
    
    # 1. Config files
    with open(os.path.join(base_dir, "package.json"), "w") as f:
        f.write('{\n  "name": "test-repo",\n  "version": "1.0.0"\n}\n')
    with open(os.path.join(base_dir, "README.md"), "w") as f:
        f.write("# Test Repo\nThis is a synthetic repository.")
    with open(os.path.join(base_dir, ".env.example"), "w") as f:
        f.write("PORT=3000\nAPI_KEY=test\n")
        
    # 2. Setup directory structure
    folders = ["src/components", "src/services", "src/utils", "tests"]
    for folder in folders:
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)
        
    file_paths = []
    for i in range(num_files):
        if i < num_files * 0.4:
            file_paths.append(f"src/components/Component{i}.ts")
        elif i < num_files * 0.7:
            file_paths.append(f"src/services/Service{i}.ts")
        elif i < num_files * 0.85:
            file_paths.append(f"src/utils/Util{i}.ts")
        else:
            file_paths.append(f"tests/Test{i}.ts")
            
    # Intentional structural anomalies
    isolated_file = file_paths[0]
    god_file = file_paths[1]
    
    total_edges = 0
    
    # 3. Generate contents with inter-dependencies
    for path in file_paths:
        full_path = os.path.join(base_dir, path)
        content = ""
        
        if path == isolated_file:
            content = "// I am completely isolated, 0 imports and 0 exports\nconst isolated = true;\n"
        elif path == god_file:
            # God class: imports many files
            imports = random.sample([p for p in file_paths if p not in (isolated_file, god_file)], min(25, len(file_paths)-2))
            for imp in imports:
                src_dir = os.path.dirname(path)
                tgt_dir = os.path.dirname(imp)
                rel_dir = os.path.relpath(tgt_dir, src_dir).replace('\\', '/')
                tgt_name = os.path.splitext(os.path.basename(imp))[0]
                
                if rel_dir == '.':
                    import_path = f"./{tgt_name}"
                elif not rel_dir.startswith('.'):
                    import_path = f"./{rel_dir}/{tgt_name}"
                else:
                    import_path = f"{rel_dir}/{tgt_name}"
                    
                content += f"import {{ something }} from '{import_path}';\n"
                total_edges += 1
            content += "\nexport class GodClass {\n  // does everything\n}\n"
        else:
            # Normal file: imports 1-4 random files
            num_imports = random.randint(1, 4)
            imports = random.sample([p for p in file_paths if p not in (isolated_file, path)], min(num_imports, len(file_paths)-2))
            for imp in imports:
                src_dir = os.path.dirname(path)
                tgt_dir = os.path.dirname(imp)
                rel_dir = os.path.relpath(tgt_dir, src_dir).replace('\\', '/')
                tgt_name = os.path.splitext(os.path.basename(imp))[0]
                
                if rel_dir == '.':
                    import_path = f"./{tgt_name}"
                elif not rel_dir.startswith('.'):
                    import_path = f"./{rel_dir}/{tgt_name}"
                else:
                    import_path = f"{rel_dir}/{tgt_name}"
                    
                content += f"import {{ stuff }} from '{import_path}';\n"
                total_edges += 1
            content += "\nexport const utilFunction = () => { return true; };\n"
            
        with open(full_path, "w") as f:
            f.write(content)
            
    # 4. Zip the output
    zip_name = f"{name}.zip"
    zip_path = os.path.join(os.getcwd(), zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                file_p = os.path.join(root, file)
                arcname = os.path.relpath(file_p, base_dir)
                zipf.write(file_p, arcname)
                
    shutil.rmtree(base_dir)
    print(f"Generated: {zip_name}")
    print(f"  Total files: {len(file_paths) + 3}")
    print(f"  Total import edges: {total_edges}")
    print(f"  Path: {zip_path}\n")

if __name__ == "__main__":
    generate_repo("test_repo_medium", "medium")
    generate_repo("test_repo_large", "large")
