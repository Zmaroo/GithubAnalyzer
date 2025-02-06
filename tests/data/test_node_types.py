from pathlib import Path

from tree_sitter_language_pack import get_binding, get_language, get_parser


def print_node_types(name, sample_file_path):
    """Print all node types in a file's AST."""
    print(f"\n=== Node types for {name} ===")
    
    try:
        parser = get_parser(name)
        with open(sample_file_path, 'rb') as f:
            code = f.read()
        
        tree = parser.parse(code)
        if tree and tree.root_node:
            # Set to store unique node types
            node_types = set()
            
            # Function to traverse the AST
            def traverse(node):
                node_types.add(node.type)
                for child in node.children:
                    traverse(child)
            
            # Traverse the tree
            traverse(tree.root_node)
            
            # Print all unique node types
            print("\nUnique node types:")
            for node_type in sorted(node_types):
                print(f"  - {node_type}")
                
            # Print first few nodes with their types and text
            print("\nFirst few nodes:")
            cursor = tree.walk()
            
            def visit_nodes():
                node = cursor.node
                text = code[node.start_byte:node.end_byte].decode('utf8')
                print(f"\nNode: {node.type}")
                print(f"Text: {text[:100]}...")
                
                if cursor.goto_first_child():
                    visit_nodes()
                    cursor.goto_parent()
                
                if cursor.goto_next_sibling():
                    visit_nodes()
            
            visit_nodes()
            
    except Exception as e:
        print(f"Error: {str(e)}")

# Get workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent.parent

# Test each language with its sample file
languages_to_test = {
    'tcl': 'sample.tcl',
    'commonlisp': 'sample.lisp',
    'ada': 'sample.adb',
    'elixir': 'sample.ex',
    'erlang': 'sample.erl'
}

for lang, sample_file in languages_to_test.items():
    sample_path = WORKSPACE_ROOT / "tests" / "data" / sample_file
    print_node_types(lang, sample_path) 