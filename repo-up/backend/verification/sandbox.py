"""
verification/sandbox.py - Isolated workspace for verification testing.
"""
import os
import shutil
import tempfile
from typing import Optional

from analysis.repair.patch_model import Patch, validate_patch, apply_patch_to_string, PatchValidationError
from .limits import MAX_WORKSPACE_SIZE_BYTES

class VerificationSandbox:
    def __init__(self, original_project_root: str):
        self.original_root = os.path.abspath(original_project_root)
        self.temp_dir = tempfile.mkdtemp(prefix="repoup_sandbox_")
        self.sandbox_root = os.path.join(self.temp_dir, "workspace")

    def setup(self) -> None:
        """Copies the original project to the isolated sandbox root."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.original_root):
            # Exclude backend venv or huge node_modules if needed, but for safety we just check size
            if 'node_modules' in dirnames:
                dirnames.remove('node_modules')
            if 'venv' in dirnames:
                dirnames.remove('venv')
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        
        if total_size > MAX_WORKSPACE_SIZE_BYTES:
            raise RuntimeError("Project exceeds MAX_WORKSPACE_SIZE_BYTES")
            
        shutil.copytree(
            self.original_root, 
            self.sandbox_root, 
            symlinks=False, 
            ignore=shutil.ignore_patterns("node_modules", "venv", ".git")
        )

    def apply_patch(self, patch: Patch) -> None:
        """Safely applies a patch inside the sandbox."""
        target_file = os.path.abspath(os.path.join(self.sandbox_root, patch.file))
        
        if not target_file.startswith(self.sandbox_root + os.sep):
            raise PatchValidationError("Patch attempts path traversal outside sandbox")
            
        if not os.path.exists(target_file):
            raise PatchValidationError("Target file does not exist in sandbox")
            
        with open(target_file, "r", encoding="utf-8") as f:
            source = f.read()
            lines = source.splitlines(keepends=True)
            
        # The validate_patch function handles path bounds, exact match, non-empty, and tree-sitter parseability
        validate_patch(patch, self.sandbox_root, lines)
        
        new_source = apply_patch_to_string(source, patch)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_source)

    def cleanup(self) -> None:
        """Removes the sandbox directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
