from fastapi import APIRouter, HTTPException
import os

router = APIRouter()

TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")

@router.get("/file-content")
async def get_file_content(session_id: str, path: str):
    """
    Returns the raw content of a file from a specific session.
    """
    if not session_id or not path:
        raise HTTPException(status_code=400, detail="Missing session_id or path")
        
    session_dir = os.path.join(TEMP_DIR, session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session expired or not found")
        
    # Prevent directory traversal
    normalized_path = os.path.normpath(path)
    if normalized_path.startswith("..") or os.path.isabs(normalized_path):
        raise HTTPException(status_code=400, detail="Invalid path")
        
    file_path = os.path.join(session_dir, normalized_path)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found in session")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
