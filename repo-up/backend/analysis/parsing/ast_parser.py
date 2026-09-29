import os
import logging

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_java
    import tree_sitter_cpp
    
    LANGUAGES = {
        "Python": Language(tree_sitter_python.language()),
        "JavaScript": Language(tree_sitter_javascript.language()),
        "TypeScript": Language(tree_sitter_typescript.language_typescript()),
        "Java": Language(tree_sitter_java.language()),
        "C++": Language(tree_sitter_cpp.language()),
    }
except ImportError as e:
    logging.warning(f"Tree-sitter or grammars not fully installed: {e}")
    LANGUAGES = {}

def parse_file(filepath: str, language: str):
    """
    Parses a source file into a Tree-sitter AST.
    Returns the AST Tree object, or None if parsing fails or file is ignored.
    """
    if language not in LANGUAGES:
        return None
        
    # Standard ignore list (skip node_modules, venv, .git, etc.)
    path_parts = filepath.split(os.sep)
    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']
    if any(part in ignored for part in path_parts):
        return None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
            
        parser = Parser(LANGUAGES[language])
        tree = parser.parse(bytes(code, "utf8"))
        return tree
    except Exception as e:
        logging.error(f"Failed to parse {filepath}: {e}")
        return None
