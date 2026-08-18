import os
import networkx as nx
from analysis.parsing.ast_parser import parse_file

def _get_language(filename: str) -> str:
    if filename.endswith('.py'):
        return 'Python'
    elif filename.endswith(('.js', '.jsx')):
        return 'JavaScript'
    elif filename.endswith(('.ts', '.tsx')):
        return 'TypeScript'
    return ''

def _extract_imports_from_tree(tree, language: str) -> list[str]:
    imports = []
    if not tree:
        return imports
    
    root_node = tree.root_node
    
    def walk(node):
        if language == 'Python':
            if node.type == 'import_from_statement':
                for child in node.children:
                    if child.type == 'dotted_name':
                        imports.append(child.text.decode('utf8'))
                        break
            elif node.type == 'import_statement':
                for child in node.children:
                    if child.type == 'dotted_name':
                        imports.append(child.text.decode('utf8'))
        elif language in ('JavaScript', 'TypeScript'):
            if node.type == 'import_statement':
                for child in node.children:
                    if child.type == 'string':
                        val = child.text.decode('utf8').strip("'\"")
                        imports.append(val)
            elif node.type == 'call_expression':
                func = None
                args = None
                for child in node.children:
                    if child.type == 'identifier':
                        func = child.text.decode('utf8')
                    elif child.type == 'arguments':
                        args = child
                if func == 'require' and args:
                    for arg in args.children:
                        if arg.type == 'string':
                            val = arg.text.decode('utf8').strip("'\"")
                            imports.append(val)
                            
        for child in node.children:
            walk(child)

    walk(root_node)
    return imports

def build_dependency_graph(root_dir: str) -> nx.DiGraph:
    graph = nx.DiGraph()
    
    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']
    file_imports = {}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        
        for f in filenames:
            lang = _get_language(f)
            if not lang:
                continue
                
            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, root_dir).replace('\\', '/')
            graph.add_node(rel_path)
            
            tree = parse_file(filepath, lang)
            if tree:
                imports = _extract_imports_from_tree(tree, lang)
                file_imports[rel_path] = imports
                
    all_nodes = set(graph.nodes())
    
    for src_file, imports in file_imports.items():
        src_dir = os.path.dirname(src_file)
        
        for imp in imports:
            if imp.startswith('./') or imp.startswith('../'):
                resolved_base = os.path.normpath(os.path.join(src_dir, imp)).replace('\\', '/')
                for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']:
                    test_path = resolved_base + ext
                    if test_path in all_nodes:
                        graph.add_edge(src_file, test_path)
                        break
            else:
                py_path = imp.replace('.', '/') if lang == 'Python' else imp
                found = False
                exts = ['.py', '/__init__.py', '', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']
                for ext in exts:
                    test_path = py_path + ext
                    if test_path in all_nodes:
                        graph.add_edge(src_file, test_path)
                        found = True
                        break
                    
                    if src_dir:
                        test_rel = os.path.normpath(os.path.join(src_dir, test_path)).replace('\\', '/')
                        if test_rel in all_nodes:
                            graph.add_edge(src_file, test_rel)
                            found = True
                            break
                
                if not found and lang in ('JavaScript', 'TypeScript'):
                    # Alias fallback: match suffix against all nodes
                    for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']:
                        suffix = py_path + ext
                        if not suffix.startswith('/'):
                            suffix = '/' + suffix
                        for node in all_nodes:
                            if node.endswith(suffix):
                                graph.add_edge(src_file, node)
                                found = True
                                break
                        if found:
                            break

    return graph

def build_dependency_graph_stream(root_dir: str):
    """
    Generator that yields ("node", rel_path) and ("edge", src, target)
    as it resolves the dependency graph.
    """
    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']
    file_imports = {}
    all_nodes = set()
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        for f in filenames:
            lang = _get_language(f)
            if not lang:
                continue
                
            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, root_dir).replace('\\', '/')
            all_nodes.add(rel_path)
            yield ("node", rel_path)
            
            tree = parse_file(filepath, lang)
            if tree:
                imports = _extract_imports_from_tree(tree, lang)
                file_imports[rel_path] = imports
                
    for src_file, imports in file_imports.items():
        src_dir = os.path.dirname(src_file)
        for imp in imports:
            if imp.startswith('./') or imp.startswith('../'):
                resolved_base = os.path.normpath(os.path.join(src_dir, imp)).replace('\\', '/')
                for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']:
                    test_path = resolved_base + ext
                    if test_path in all_nodes:
                        yield ("edge", src_file, test_path)
                        break
            else:
                py_path = imp.replace('.', '/') if lang == 'Python' else imp
                found = False
                exts = ['.py', '/__init__.py', '', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']
                for ext in exts:
                    test_path = py_path + ext
                    if test_path in all_nodes:
                        yield ("edge", src_file, test_path)
                        found = True
                        break
                    
                    if src_dir:
                        test_rel = os.path.normpath(os.path.join(src_dir, test_path)).replace('\\', '/')
                        if test_rel in all_nodes:
                            yield ("edge", src_file, test_rel)
                            found = True
                            break
                
                if not found and lang in ('JavaScript', 'TypeScript'):
                    # Alias fallback: match suffix against all nodes
                    for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']:
                        suffix = py_path + ext
                        if not suffix.startswith('/'):
                            suffix = '/' + suffix
                        for node in all_nodes:
                            if node.endswith(suffix):
                                yield ("edge", src_file, node)
                                found = True
                                break
                        if found:
                            break

def serialize_graph(graph: nx.DiGraph) -> dict:
    """Serializes a networkx DiGraph into a JSON-friendly dict."""
    return {
        "nodes": [{"id": n, "label": os.path.basename(n)} for n in graph.nodes()],
        "edges": [{"source": u, "target": v} for u, v in graph.edges()]
    }
