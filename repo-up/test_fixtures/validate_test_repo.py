import os
import zipfile

def validate():
    zip_path = "repo-up-comprehensive-test.zip"
    assert os.path.exists(zip_path), "ZIP file missing"
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        
    def check_ext(ext):
        return any(f.endswith(ext) for f in files)
        
    assert check_ext(".py"), "Python files missing"
    assert check_ext(".js"), "JS files missing"
    assert check_ext(".ts"), "TS files missing"
    assert check_ext(".java"), "Java files missing"
    assert check_ext(".cpp"), "C++ files missing"
    
    print(f"Validation successful! {len(files)} files checked in {zip_path}")
    
if __name__ == "__main__":
    validate()
