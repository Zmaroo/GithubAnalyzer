import os
import tree_sitter_c_sharp as tscsharp
from tree_sitter import Language, Parser

CSHARP_LANGUAGE = Language(tscsharp.language())

parser = Parser(CSHARP_LANGUAGE)

def node_to_sexp(node, source_code):
    if node.child_count == 0:
        text = source_code[node.start_byte:node.end_byte].decode('utf-8').strip()
        return f"({node.type} \"{text}\")"
    else:
        children_sexp = " ".join(node_to_sexp(child, source_code) for child in node.children)
        return f"({node.type} {children_sexp})"

def main():
    sample_path = os.path.join(os.path.dirname(__file__), 'sample.cs')
    with open(sample_path, 'rb') as f:
        source_code = f.read()

    # Parse the C# source code
    tree = parser.parse(source_code)

    # Output the syntax tree in s-expression form
    print('C# Syntax Tree (s-expression):')
    print(node_to_sexp(tree.root_node, source_code))


if __name__ == '__main__':
    main() 