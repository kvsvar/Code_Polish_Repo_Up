"""
routes/repair.py — POST /repair

Accepts a finding dict and a session_id, returns a candidate patch.

Response shape
--------------
{
    "finding": {...},
    "repair_available": bool,
    "tier": "tier1_deterministic" | "tier2_suggested" | "tier3_explanation_only" | null,
    "verification_status": "not_verified",
    "patch": {                         # only for Tier 1 when a patch was generated
        "rule_id": "...",
        "language": "...",
        "file": "...",
        "start_line": int,
        "old_text": "...",
        "new_text": "...",
        "diff": "...",
        "verification_status": "not_verified"
    } | null,
    "validation_error": "..." | null,  # why a Tier 1 patch failed, if applicable
    "explanation": "..."               # always present for Tier 2/3
}

The endpoint never modifies files. verification_status is always "not_verified".
"""

import logging
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()
log = logging.getLogger(__name__)

# Sessions map session_id → project_path (populated by handle_uploaded_zip)
# We import the same module the upload service uses.
from services.upload_service import SESSION_STORE


class RepairRequest(BaseModel):
    session_id: str
    finding: dict


@router.post("/repair")
async def request_repair(body: RepairRequest) -> JSONResponse:
    """Generate a candidate patch for a finding.

    Does NOT apply the patch.
    Does NOT execute any modified code.
    verification_status is always 'not_verified'.
    """
    session_id = body.session_id
    finding = body.finding

    # Resolve project_root from session store
    session = SESSION_STORE.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session not found or expired. Please re-upload the project.",
                }
            },
        )

    project_root = session.get("project_path", "")
    if not project_root or not os.path.isdir(project_root):
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "PROJECT_PATH_MISSING",
                    "message": "Project path for this session is no longer available.",
                }
            },
        )

    try:
        from analysis.repair.repair_engine import get_candidate_patch
        from verification.runner import verify_patch
        from analysis.finding import Finding
        
        response = get_candidate_patch(finding, project_root)
        
        # Phase 11: Optional LLM-Assisted Explanation and Patch Suggestion
        if not response.patch:
            from llm.llm_engine import explain_and_suggest_patch
            llm_explanation, llm_patch = explain_and_suggest_patch(finding, project_root)
            
            if llm_explanation and "unavailable" not in llm_explanation:
                response.explanation = llm_explanation
                
            if llm_patch:
                response.patch = llm_patch
                response.tier = "tier2_suggested"
        
        # Phase 6: Safely verify the patch
        if response.patch:
            f = Finding.from_dict(finding)
            ver_result = verify_patch(project_root, response.patch, f)
            response.patch.verification_status = ver_result.status.value
            
            # Serialize the response dict
            resp_dict = response.to_dict()
            resp_dict["patch"]["verification_details"] = ver_result.to_dict()
            return JSONResponse(content=resp_dict)
            
        return JSONResponse(content=response.to_dict())
    except Exception:
        log.exception("Repair engine failed for session=%s rule=%s",
                      session_id, finding.get("rule_id"))
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "REPAIR_ENGINE_ERROR",
                    "message": "Repair engine encountered an unexpected error.",
                }
            },
        )
