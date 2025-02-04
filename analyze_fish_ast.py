from tree_sitter_language_pack import get_parser
from pathlib import Path
import json
import os

def analyze_node(node, source_bytes):
    """Analyze a node and its children recursively."""
    result = {
        'type': node.type,
        'text': node.text.decode('utf8') if hasattr(node, 'text') else None,
        'start_point': node.start_point,
        'end_point': node.end_point,
        'children': []
    }
    
    # Add field information if available
    if hasattr(node, 'fields'):
        result['fields'] = {
            name: [analyze_node(child, source_bytes) for child in field]
            for name, field in node.fields().items()
        }
    
    # Recursively analyze children
    for child in node.children:
        result['children'].append(analyze_node(child, source_bytes))
    
    return result

def main():
    # Get the Fish parser
    parser = get_parser('fish')
    
    # Read the sample file
    sample_path = Path('tests/data/sample.fish')
    with open(sample_path, 'r') as f:
        source = f.read()
    
    # Parse the file
    tree = parser.parse(bytes(source, 'utf8'))
    print(f"Successfully parsed Fish file")
    print(f"Root node type: {tree.root_node.type}")
    print(f"Number of child nodes: {len(tree.root_node.children)}")
    
    # Analyze the AST
    ast = analyze_node(tree.root_node, bytes(source, 'utf8'))
    
    # Write the AST to a file in current directory
    output_path = Path('@fish-node-types.json')
    with open(output_path, 'w') as f:
        json.dump(ast, f, indent=2)
    
    print(f"\nAST analysis written to {output_path}")

if __name__ == '__main__':
    main() 