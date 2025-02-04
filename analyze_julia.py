from GithubAnalyzer.services.analysis.parsers.traversal_service import TreeSitterTraversal
from tree_sitter_language_pack import get_binding, get_language, get_parser

def analyze_julia_ast():
    # Initialize services
    traversal = TreeSitterTraversal()

    # Get Julia parser
    julia_parser = get_parser('julia')

    # Parse the file
    with open("tests/data/sample.jl", "rb") as f:
        tree = julia_parser.parse(f.read())

    print("\nJulia AST Structure:\n")
    
    def print_node(node, depth=0):
        indent = "  " * depth
        node_info = traversal.get_node_info(node)
        print(f"{indent}Node Type: {node_info['type']}")
        print(f"{indent}Text: {traversal.get_node_text(node)}")
        
        # Print field names for children
        if node.children:
            print(f"{indent}Children:")
            for child in node.children:
                field_name = node.field_name_for_child(node.children.index(child))
                field_info = f" ({field_name})" if field_name else ""
                print(f"{indent}  - {child.type}{field_info}")
                print_node(child, depth + 2)

    # Print full tree structure
    print_node(tree.root_node)

if __name__ == "__main__":
    analyze_julia_ast() 