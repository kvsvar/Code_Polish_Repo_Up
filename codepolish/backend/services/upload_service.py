import os
import shutil
import zipfile
import uuid
from fastapi import UploadFile, HTTPException

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

async def handle_uploaded_zip(file: UploadFile) -> tuple[str, int, int]:
    """
    Saves the uploaded zip file to the temp directory, extracts it,
    deletes the original zip, and returns (path, file_count, folder_count).
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    zip_path = os.path.join(session_dir, file.filename)
    
    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(session_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file uploaded.")
            
        os.remove(zip_path)
        
        from utils.detector import detect_project_details
        file_count, folder_count, languages, frameworks = detect_project_details(session_dir)
            
        return session_dir, file_count, folder_count, languages, frameworks
        
    except HTTPException:
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        raise
    except Exception as e:
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        raise HTTPException(status_code=500, detail=f"Failed to process zip file: {str(e)}")
