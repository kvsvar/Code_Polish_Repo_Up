from fastapi import APIRouter, UploadFile, File, HTTPException
from services.upload_service import handle_uploaded_zip
import logging

router = APIRouter()

@router.post("/analyze")
async def analyze_project(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are supported for upload.")
    
    try:
        project_path, file_count, folder_count, detected_languages, detected_frameworks = await handle_uploaded_zip(file)
        
        language = None
        if len(detected_languages) == 1:
            language = detected_languages[0]
        elif len(detected_languages) > 1:
            language = detected_languages
            
        framework = None
        if len(detected_frameworks) == 1:
            framework = detected_frameworks[0]
        elif len(detected_frameworks) > 1:
            framework = detected_frameworks
            
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from analysis.rules.structural import run_structural_rules
        from services.tree_service import generate_project_tree
        
        findings, score = run_structural_rules(project_path)
        tree = generate_project_tree(project_path)
            
        return {
            "language": language,
            "framework": framework,
            "files": file_count,
            "folders": folder_count,
            "score": score,
            "issues": findings,
            "tree": tree
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to process upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process uploaded project.")
