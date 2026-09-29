import networkx as nx
from analysis.finding import Finding
from analysis.rule_registry import get as get_rule

def afferent_couplings(graph: nx.DiGraph, node: str) -> int:
    """Incoming edges -- CK's afferent coupling / in-degree."""
    if node not in graph:
        return 0
    return graph.in_degree(node)

def cof(graph: nx.DiGraph) -> float:
    """Coupling Factor -- system-level connectivity.
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
    """Detect files with high Coupling Between Objects (CBO).

    Returns serialised finding dicts for backwards compatibility with analyze.py.
    Internally builds Finding objects so rule_id and resolution are available.
    """
    spec = get_rule("METRIC-HIGH-CBO")
    findings = []
    for node in graph.nodes():
        total_coupling = graph.in_degree(node) + graph.out_degree(node)
        if total_coupling >= threshold:
            finding = Finding(
                rule_id="METRIC-HIGH-CBO",
                category="Metrics",
                title="High CBO (Coupling Between Objects)",
                description=f"File '{node}' has high coupling ({total_coupling} connections). High coupling makes the file fragile to changes.",
                severity="Medium",
                rule=spec.name if spec else "High CBO",
                resolution=spec.resolution if spec else None,
                file=node,
            )
            findings.append(finding.to_dict())
    return findings
