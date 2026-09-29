"""
main.py — FastAPI application entry point for Repo-Up.

All API errors return {"error": {"code": "...", "message": "..."}} per Rules.md.
Raw stack traces and exception strings are never sent to the client.
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from routes import analyze, tree, file, repair

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Repo-Up API")

# ---------------------------------------------------------------------------
# CORS — frontend dev server only
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global error handlers — structured {"error": {"code", "message"}}
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return HTTPExceptions in the structured error envelope.

    If the detail is already our {"error": {...}} dict, pass it through.
    Otherwise wrap it.
    """
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        body = detail
    else:
        body = {"error": {"code": "REQUEST_ERROR", "message": str(detail) if detail else "An error occurred."}}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422 validation errors without leaking internal field paths."""
    logging.warning("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed. Check the required parameters.",
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all — log with context, never expose internals to the client."""
    logging.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
            }
        },
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(analyze.router)
app.include_router(tree.router)
app.include_router(file.router)
app.include_router(repair.router)


@app.get("/")
def read_root() -> dict:
    return {"message": "Repo-Up API is running"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> JSONResponse:
    return JSONResponse(status_code=204, content=None)
