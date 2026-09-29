"""
routes/analyze.py — POST /analyze

Accepts a ZIP upload, extracts it, and streams analysis progress back to the
client as Server-Sent Events (SSE).

SSE event types
---------------
{"type": "file",  "path": "..."}          — a source file was discovered
{"type": "edge",  "source": "...", "target": "..."} — a dependency edge
{"type": "done",  "result": {...}}         — final analysis result
{"type": "error", "error": {"code": "...", "message": "..."}}
                                           — analysis failed after stream started

Graceful degradation (Rules.md §2)
-----------------------------------
Each analysis stage runs inside its own try/except. A single failing check logs
the error on the server side and is skipped; it does NOT abort the whole run.
"""

import json
import logging
import asyncio
import os
import sys
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from services.upload_service import handle_uploaded_zip

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_project(file: UploadFile = File(...)) -> StreamingResponse:
    """Accept a ZIP, run the full analysis pipeline, stream results."""
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": "Only .zip files are supported.",
                }
            },
        )

    try:
        (
            project_path,
            file_count,
            folder_count,
            detected_languages,
            detected_frameworks,
            session_id,
        ) = await handle_uploaded_zip(file)
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Upload handling failed")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ANALYSIS_FAILED",
                    "message": "Failed to process the uploaded project.",
                }
            },
        ) from exc

    language = (
        detected_languages[0]
        if len(detected_languages) == 1
        else detected_languages
        if detected_languages
        else None
    )
    framework = (
        detected_frameworks[0]
        if len(detected_frameworks) == 1
        else detected_frameworks
        if detected_frameworks
        else None
    )

    async def event_generator():  # noqa: C901  (complexity OK here — it's a pipeline)
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        import networkx as nx
        from analysis.rules.structural import run_structural_rules
        from analysis.rules.security import run_security_rules
        from analysis.rules.ast_security import run_ast_security_rules
        from services.tree_service import generate_project_tree
        from services.graph_service import build_dependency_graph_stream, serialize_graph
        from analysis.metrics.graph_metrics import (
            cof,
            afferent_couplings,
            detect_circular_dependencies,
            detect_high_cbo,
        )
        from analysis.metrics.class_metrics import calculate_repo_averages
        from analysis.scorer import compute_repo_score
        from analysis.finding import Finding
        from analysis.rule_registry import get as get_rule
        from analysis.rules.smells.smell_engine import run_smell_engine
        from analysis.rules.security.security_engine import run_security_engine

        try:
            graph = nx.DiGraph()
            findings: list[dict] = []

            # ------------------------------------------------------------------
            # Stage 1 — stream dependency graph nodes/edges
            # ------------------------------------------------------------------
            try:
                for event in build_dependency_graph_stream(project_path):
                    if event[0] == "node":
                        graph.add_node(event[1])
                        yield f"data: {json.dumps({'type': 'file', 'path': event[1]})}\n\n"
                    elif event[0] == "edge":
                        graph.add_edge(event[1], event[2])
                        yield f"data: {json.dumps({'type': 'edge', 'source': event[1], 'target': event[2]})}\n\n"
                    await asyncio.sleep(0.01)
            except Exception:
                log.exception("Stage 1 (graph build) failed — continuing without graph edges")

            # ------------------------------------------------------------------
            # Stage 2 — structural rules
            # ------------------------------------------------------------------
            score = 100
            try:
                struct_findings, score = run_structural_rules(project_path)
                findings.extend(struct_findings)
            except Exception:
                log.exception("Stage 2 (structural rules) failed — skipping")

            # ------------------------------------------------------------------
            # Stage 3 — security rules (regex-based)
            # ------------------------------------------------------------------
            security_score = 100
            try:
                sec_findings_1, sec_penalty_1 = run_security_rules(project_path)
                findings.extend(sec_findings_1)
                security_score -= sec_penalty_1
            except Exception:
                log.exception("Stage 3a (regex security) failed — skipping")

            # ------------------------------------------------------------------
            # Stage 4 — AST security rules
            # ------------------------------------------------------------------
            try:
                sec_findings_2, sec_penalty_2 = run_ast_security_rules(project_path)
                findings.extend(sec_findings_2)
                security_score -= sec_penalty_2
            except Exception:
                log.exception("Stage 4 (AST security) failed — skipping")

            security_score = max(0, min(100, security_score))

            # ------------------------------------------------------------------
            # Stage 5 — circular dependency detection (Tarjan SCC)
            # ------------------------------------------------------------------
            try:
                cycles = detect_circular_dependencies(graph)
                seen_cycles: set[frozenset] = set()
                for cycle in cycles:
                    key = frozenset(cycle)
                    if key in seen_cycles:
                        continue
                    seen_cycles.add(key)
                    first_file = sorted(cycle)[0]  # deterministic representative
                    rule_spec = get_rule("STRUCT-CIRCULAR-DEP")
                    finding = Finding(
                        rule_id="STRUCT-CIRCULAR-DEP",
                        category="Structural",
                        title="Circular Dependency Detected",
                        description=(
                            f"Circular dependency detected involving: {', '.join(sorted(cycle))}. "
                            "This makes the module hierarchy harder to reason about and test."
                        ),
                        severity="High",
                        rule=rule_spec.name if rule_spec else "Circular Dependency",
                        resolution=rule_spec.resolution if rule_spec else None,
                        file=first_file,
                        line=1,
                    )
                    findings.append(finding.to_dict())
                    score -= 15
                score = max(0, min(100, score))
            except Exception:
                log.exception("Stage 5 (circular deps) failed — skipping")

            # ------------------------------------------------------------------
            # Stage 6 — class/module metrics (CK-style)
            # ------------------------------------------------------------------
            class_avgs: dict = {
                "avg_public_fields": 0.0,
                "avg_public_methods": 0.0,
                "avg_dit": 1.0,
                "avg_lcom": 0.0,
            }
            try:
                class_avgs, metric_findings = calculate_repo_averages(project_path)
                findings.extend(metric_findings)
            except Exception:
                log.exception("Stage 6 (class metrics) failed — skipping")

            # ------------------------------------------------------------------
            # Stage 7 — graph-level metrics (COF, afferent, CBO)
            # ------------------------------------------------------------------
            sys_cof = 0.0
            avg_afferent = 0.0
            try:
                sys_cof = cof(graph)
                n = graph.number_of_nodes()
                avg_afferent = (
                    sum(afferent_couplings(graph, nd) for nd in graph.nodes()) / n
                    if n > 0
                    else 0.0
                )
                cbo_findings = detect_high_cbo(graph)
                findings.extend(cbo_findings)
            except Exception:
                log.exception("Stage 7 (graph metrics) failed -- skipping")

            # ------------------------------------------------------------------
            # Stage 8 -- code smell engine (Phase 2)
            # ------------------------------------------------------------------
            try:
                smell_findings, smell_penalty = run_smell_engine(project_path)
                findings.extend(smell_findings)
                # Smell penalty reduces structural score
                score = max(0, score - smell_penalty)
            except Exception:
                log.exception("Stage 8 (smell engine) failed -- skipping")

            # ------------------------------------------------------------------
            # Stage 9 -- Phase 3 security engine (CWE-tagged rules)
            # ------------------------------------------------------------------
            try:
                sec3_findings, sec3_penalty = run_security_engine(project_path)
                findings.extend(sec3_findings)
                security_score = max(0, security_score - sec3_penalty)
            except Exception:
                log.exception("Stage 9 (security engine) failed -- skipping")

            # ------------------------------------------------------------------
            # Scoring
            # ------------------------------------------------------------------
            repo_metrics = {
                "cof": sys_cof,
                "avg_afferent": avg_afferent,
                "avg_public_fields": class_avgs.get("avg_public_fields", 0.0),
                "avg_public_methods": class_avgs.get("avg_public_methods", 0.0),
                "avg_dit": class_avgs.get("avg_dit", 1.0),
                "avg_lcom": class_avgs.get("avg_lcom", 0.0),
            }
            rubric = compute_repo_score(repo_metrics, score, security_score)

            # ------------------------------------------------------------------
            # Build result and emit "done" event
            # ------------------------------------------------------------------
            tree = generate_project_tree(project_path)

            result = {
                "language": language,
                "framework": framework,
                "files": file_count,
                "folders": folder_count,
                "score": score,
                "issues": findings,
                "tree": tree,
                "rubric": rubric,
                "graph": serialize_graph(graph),
                "session_id": session_id,
            }
            yield f"data: {json.dumps({'type': 'done', 'result': result})}\n\n"

        except Exception:
            # The stream has already started — emit an error event so the
            # frontend can show a toast rather than hanging forever.
            log.exception("Analysis pipeline failed after stream started (session=%s)", session_id)
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "error": {
                            "code": "ANALYSIS_FAILED",
                            "message": "Analysis encountered an unexpected error. Please try again.",
                        },
                    }
                )
                + "\n\n"
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
