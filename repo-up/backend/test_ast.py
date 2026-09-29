import os
import sys

# Add backend directory to sys.path so we can import analysis module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.parsing.ast_parser import parse_file

def main():
    test_file = os.path.join(os.path.dirname(__file__), "main.py")
    
    print(f"Testing AST parsing on {test_file}")
    
    tree = parse_file(test_file, "Python")
    
    if tree is None:
        print("Failed to parse or file was ignored.")
        return
        
    root_node = tree.root_node
    print(f"Successfully parsed!")
    print(f"Root node type: {root_node.type}")
    print(f"Number of children: {len(root_node.children)}")
    
    # Just to show it's walkable
    for i, child in enumerate(root_node.children[:3]):
        print(f"  Child {i}: {child.type}")
        
    print("\nTesting ignore list:")
    ignored_file = os.path.join(os.path.dirname(__file__), "node_modules", "test.py")
    tree2 = parse_file(ignored_file, "Python")
    if tree2 is None:
        print(f"Successfully ignored {ignored_file}")
    else:
        print(f"Failed to ignore {ignored_file}!")

if __name__ == "__main__":
    main()
