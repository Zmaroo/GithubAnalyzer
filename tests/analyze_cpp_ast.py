from tree_sitter_language_pack import get_binding, get_language, get_parser


def print_node(cursor, level=0):
    node = cursor.node
    print('  ' * level + f'{node.type}: {node.text.decode()} ({node.start_point}, {node.end_point})')
    
    if cursor.goto_first_child():
        while True:
            print_node(cursor, level + 1)
            if not cursor.goto_next_sibling():
                break
        cursor.goto_parent()

def main():
    # Get the C++ parser from the language pack
    cpp_parser = get_parser('cpp')
    
    # Parse the sample file
    with open('tests/data/sample.cpp', 'r') as f:
        tree = cpp_parser.parse(bytes(f.read(), 'utf8'))
    
    cursor = tree.walk()
    print_node(cursor)

if __name__ == '__main__':
    main() 