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
