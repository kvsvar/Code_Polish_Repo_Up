import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.graph_service import build_dependency_graph
from analysis.metrics.graph_metrics import cof, afferent_couplings

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Building dependency graph for: {project_root}")
    
    graph = build_dependency_graph(project_root)
    
    print(f"\nNodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")
    
    app_tsx = "src/App.tsx"
    
    if app_tsx in graph:
        print(f"\nFound {app_tsx} in graph.")
        out_edges = list(graph.successors(app_tsx))
        print(f"Imports from {app_tsx}: {out_edges}")
    else:
        print(f"\nWARNING: {app_tsx} not found in graph.")
        
    landing_tsx = "src/components/Landing.tsx"
    
    print(f"\nAfferent Couplings for {landing_tsx}: {afferent_couplings(graph, landing_tsx)}")
    
    c = cof(graph)
    print(f"\nSystem COF: {c:.4f}")

if __name__ == "__main__":
    main()
