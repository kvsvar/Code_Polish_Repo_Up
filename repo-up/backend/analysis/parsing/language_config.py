LANGUAGE_CONFIG = {
    "Java": {
        "extensions": [".java"],
        "class_nodes": ["class_declaration"],
        "method_nodes": ["method_declaration"],
        "import_nodes": ["import_declaration"],
        "inheritance_nodes": ["superclass", "interfaces"],
        "try_nodes": ["try_statement", "try_with_resources_statement"],
        "call_nodes": ["method_invocation"],
        "is_oo": True
    },
    "C++": {
        "extensions": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
        "class_nodes": ["class_specifier", "struct_specifier"],
        "method_nodes": ["function_definition"],
        "import_nodes": ["preproc_include"],
        "inheritance_nodes": ["base_class_clause"],
        "try_nodes": ["try_statement"],
        "call_nodes": ["call_expression"],
        "is_oo": True
    },
    "Python": {
        "extensions": [".py"],
        "class_nodes": ["class_definition"],
        "method_nodes": ["function_definition"],
        "import_nodes": ["import_statement", "import_from_statement"],
        "inheritance_nodes": ["argument_list"],
        "try_nodes": ["try_statement"],
        "call_nodes": ["call"],
        "is_oo": True
    },
    "JavaScript": {
        "extensions": [".js", ".jsx"],
        "class_nodes": ["class_declaration"],
        "method_nodes": ["method_definition", "function_declaration", "lexical_declaration", "variable_declaration"],
        "import_nodes": ["import_statement", "call_expression"],
        "inheritance_nodes": ["class_heritage"],
        "try_nodes": ["try_statement"],
        "call_nodes": ["call_expression"],
        "is_oo": True
    },
    "TypeScript": {
        "extensions": [".ts", ".tsx"],
        "class_nodes": ["class_declaration"],
        "method_nodes": ["method_definition", "function_declaration", "lexical_declaration", "variable_declaration"],
        "import_nodes": ["import_statement", "call_expression"],
        "inheritance_nodes": ["class_heritage"],
        "try_nodes": ["try_statement"],
        "call_nodes": ["call_expression"],
        "is_oo": True
    }
}
