"""
upload_service.py — handles ZIP upload, extraction, and basic validation.

Security model
--------------
* Client filename is NEVER used on disk; we always write to a fixed name.
* Every archive member path is resolved and must stay inside the session dir
  (zip-slip protection).
* Absolute paths and symlink entries are rejected.
* Hard limits guard against zip-bomb attacks.
"""

import os
import shutil
import zipfile
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

# ---------------------------------------------------------------------------
# Configurable limits (tune here, never in-code)
# ---------------------------------------------------------------------------
MAX_UPLOAD_BYTES: int = 50 * 1024 * 1024        # 50 MB compressed
MAX_UNCOMPRESSED_BYTES: int = 300 * 1024 * 1024  # 300 MB uncompressed total
MAX_FILE_COUNT: int = 5_000                       # entries in archive

# Place temp dir outside the backend/ directory to avoid triggering uvicorn --reload on every upload
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp")

# Session store: maps session_id (str) → {"project_path": str}
# Used by the repair endpoint to resolve a session back to its extracted directory.
SESSION_STORE: dict[str, dict] = {}


async def handle_uploaded_zip(
    file: UploadFile,
) -> tuple[str, int, int, list[str], list[str], str]:
    """Save, validate, and extract an uploaded ZIP file.

    Returns
    -------
    (project_path, file_count, folder_count, languages, frameworks, session_id)
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    _cleanup_old_sessions()

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Use a fixed filename — never trust client-supplied names.
    zip_path = os.path.join(session_dir, "upload.zip")

    try:
        # --- Read & size-check compressed data --------------------------------
        raw = await file.read()
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": {
                        "code": "ARCHIVE_TOO_LARGE",
                        "message": f"Uploaded archive exceeds the {MAX_UPLOAD_BYTES // (1024*1024)} MB limit.",
                    }
                },
            )

        with open(zip_path, "wb") as buf:
            buf.write(raw)
        del raw  # free memory early

        # --- Validate and extract the ZIP ------------------------------------
        try:
            zf = zipfile.ZipFile(zip_path, "r")
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_ARCHIVE",
                        "message": "The uploaded file is not a valid ZIP archive.",
                    }
                },
            )

        with zf:
            members = zf.infolist()

            # Entry-count guard
            if len(members) > MAX_FILE_COUNT:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "code": "ARCHIVE_TOO_LARGE",
                            "message": f"Archive contains more than {MAX_FILE_COUNT} entries.",
                        }
                    },
                )

            # Uncompressed-size guard and zip-slip check
            total_uncompressed = 0
            session_path = Path(session_dir).resolve()

            for member in members:
                # Reject symlinks
                is_symlink = (member.external_attr >> 16) & 0xA000 == 0xA000
                if is_symlink:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": {
                                "code": "INVALID_ARCHIVE",
                                "message": "Archive contains symlink entries, which are not allowed.",
                            }
                        },
                    )

                # Reject absolute paths
                if os.path.isabs(member.filename):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": {
                                "code": "INVALID_ARCHIVE",
                                "message": "Archive contains absolute path entries.",
                            }
                        },
                    )

                # Zip-slip: resolve target and verify it stays inside session_dir
                target = (session_path / member.filename).resolve()
                try:
                    target.relative_to(session_path)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": {
                                "code": "INVALID_ARCHIVE",
                                "message": "Archive contains path traversal entries (zip-slip attack rejected).",
                            }
                        },
                    )

                total_uncompressed += member.file_size
                if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": {
                                "code": "ARCHIVE_TOO_LARGE",
                                "message": f"Uncompressed archive contents exceed the {MAX_UNCOMPRESSED_BYTES // (1024*1024)} MB safety limit.",
                            }
                        },
                    )

            zf.extractall(session_dir)

        os.remove(zip_path)

        from utils.detector import detect_project_details

        file_count, folder_count, languages, frameworks = detect_project_details(session_dir)

        # Register session so the repair endpoint can resolve project_path.
        SESSION_STORE[session_id] = {"project_path": session_dir}

        return session_dir, file_count, folder_count, languages, frameworks, session_id

    except HTTPException:
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir, ignore_errors=True)
        raise
    except Exception as exc:
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ANALYSIS_FAILED",
                    "message": "Failed to process the uploaded archive.",
                }
            },
        ) from exc


def _cleanup_old_sessions(max_age_seconds: int = 7_200) -> None:
    """Delete session directories older than *max_age_seconds* (default 2 h).

    Only deletes directories directly inside TEMP_DIR — never touches anything
    outside that directory.
    """
    if not os.path.isdir(TEMP_DIR):
        return
    import time

    now = time.time()
    try:
        for entry in os.scandir(TEMP_DIR):
            if not entry.is_dir():
                continue
            try:
                age = now - entry.stat().st_mtime
                if age > max_age_seconds:
                    shutil.rmtree(entry.path, ignore_errors=True)
            except Exception:
                pass  # Skip entries we can't stat — never raise during cleanup
    except Exception:
        pass
