import networkx as nx

def afferent_couplings(graph: nx.DiGraph, node: str) -> int:
    """Incoming edges — CK's afferent coupling / in-degree."""
    if node not in graph:
        return 0
    return graph.in_degree(node)

def cof(graph: nx.DiGraph) -> float:
    """Coupling Factor — system-level connectivity.
    COF = actual_connections / (n^2 - n), per Ferreira et al. 2012."""
    n = graph.number_of_nodes()
    c = graph.number_of_edges()
    return c / (n * n - n) if n > 1 else 0.0

def detect_circular_dependencies(graph: nx.DiGraph) -> list[list[str]]:
    """
    Uses Tarjan's Strongly Connected Components algorithm to detect circular dependencies.
    Returns a list of strongly connected components that have more than 1 node (i.e., cycles).
    """
    cycles = []
    for component in nx.strongly_connected_components(graph):
        if len(component) > 1:
            cycles.append(list(component))
    return cycles

def detect_high_cbo(graph: nx.DiGraph, threshold=5) -> list[dict]:
    findings = []
    for node in graph.nodes():
        total_coupling = graph.in_degree(node) + graph.out_degree(node)
        if total_coupling >= threshold:
            findings.append({
                "category": "Metrics",
                "title": "High CBO (Coupling Between Objects)",
                "description": f"File '{node}' has high coupling ({total_coupling} connections). High coupling makes the file fragile to changes.",
                "severity": "Medium",
                "file": node
            })
    return findings
