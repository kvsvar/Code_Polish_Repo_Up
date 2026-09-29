from fastapi import APIRouter, HTTPException, Query
import os

router = APIRouter()

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.tree_service import generate_project_tree

@router.get("/tree")
async def get_project_tree(project_path: str = Query(..., description="Path to the extracted project")):
    if not os.path.exists(project_path) or not os.path.isdir(project_path):
        raise HTTPException(status_code=404, detail="Project path not found")
        
    return generate_project_tree(project_path)
