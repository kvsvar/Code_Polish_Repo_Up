from fastapi import APIRouter, UploadFile, File, HTTPException
from services.upload_service import handle_uploaded_zip
import logging

router = APIRouter()

@router.post("/analyze")
async def analyze_project(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are supported for upload.")
    
    try:
        project_path, file_count, folder_count, detected_languages, detected_frameworks, session_id = await handle_uploaded_zip(file)
        
        language = detected_languages[0] if len(detected_languages) == 1 else detected_languages if detected_languages else None
        framework = detected_frameworks[0] if len(detected_frameworks) == 1 else detected_frameworks if detected_frameworks else None
            
        async def event_generator():
            import sys
            import os
            import json
            import asyncio
            import networkx as nx
            
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from analysis.rules.structural import run_structural_rules
            from analysis.rules.security import run_security_rules
            from analysis.rules.ast_security import run_ast_security_rules
            from services.tree_service import generate_project_tree
            from services.graph_service import build_dependency_graph_stream, serialize_graph
            from analysis.metrics.graph_metrics import cof, afferent_couplings, detect_circular_dependencies, detect_high_cbo
            from analysis.metrics.class_metrics import calculate_repo_averages
            from analysis.scorer import compute_repo_score
            
            graph = nx.DiGraph()
            
            # Stream graph building
            for event in build_dependency_graph_stream(project_path):
                if event[0] == "node":
                    graph.add_node(event[1])
                    yield f"data: {json.dumps({'type': 'file', 'path': event[1]})}\n\n"
                elif event[0] == "edge":
                    graph.add_edge(event[1], event[2])
                    yield f"data: {json.dumps({'type': 'edge', 'source': event[1], 'target': event[2]})}\n\n"
                
                await asyncio.sleep(0.01) # Small sleep to yield to event loop and simulate live pacing
                
            # Finish analysis
            findings, score = run_structural_rules(project_path)
            
            # Run security rules
            sec_findings_1, sec_penalty_1 = run_security_rules(project_path)
            sec_findings_2, sec_penalty_2 = run_ast_security_rules(project_path)
            
            findings.extend(sec_findings_1)
            findings.extend(sec_findings_2)
            
            security_score = 100 - (sec_penalty_1 + sec_penalty_2)
            security_score = max(0, security_score)
            
            # Detect circular dependencies using Tarjan's SCC
            cycles = detect_circular_dependencies(graph)
            for cycle in cycles:
                findings.append({
                    "category": "Structural",
                    "title": "Circular Dependency Detected",
                    "description": f"Detected a circular dependency (via Tarjan's SCC) involving: {', '.join(cycle)}",
                    "severity": "High"
                })
                score -= 15
            
            score = max(0, score)
            
            tree = generate_project_tree(project_path)
            
            sys_cof = cof(graph)
            if graph.number_of_nodes() > 0:
                avg_afferent = sum(afferent_couplings(graph, n) for n in graph.nodes()) / graph.number_of_nodes()
            else:
                avg_afferent = 0.0
                
            class_avgs, metric_findings = calculate_repo_averages(project_path)
            
            # Detect High CBO (Coupling)
            cbo_findings = detect_high_cbo(graph)
            
            findings.extend(metric_findings)
            findings.extend(cbo_findings)
            repo_metrics = {
                "cof": sys_cof,
                "avg_afferent": avg_afferent,
                "avg_public_fields": class_avgs["avg_public_fields"],
                "avg_public_methods": class_avgs["avg_public_methods"],
                "avg_dit": class_avgs["avg_dit"],
                "avg_lcom": class_avgs["avg_lcom"]
            }
            
            rubric = compute_repo_score(repo_metrics, score, security_score)
                
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
                "session_id": session_id
            }
            yield f"data: {json.dumps({'type': 'done', 'result': result})}\n\n"

        from fastapi.responses import StreamingResponse
        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to process upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process uploaded project.")
