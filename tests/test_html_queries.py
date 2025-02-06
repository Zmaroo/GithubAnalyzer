from pathlib import Path

from tree_sitter_language_pack import get_parser

from GithubAnalyzer.services.analysis.parsers.query_patterns import \
    QUERY_PATTERNS


def test_html_patterns():
    # Get the HTML parser
    parser = get_parser('html')
    
    # Read the sample file
    sample_path = Path('tests/data/sample.html')
    with open(sample_path, 'r') as f:
        source = f.read()
    
    # Parse the file
    tree = parser.parse(bytes(source, 'utf8'))
    print(f"Successfully parsed HTML file")
    print(f"Root node type: {tree.root_node.type}")
    print(f"Number of child nodes: {len(tree.root_node.children)}")
    
    # Test each pattern
    for pattern_name, pattern in QUERY_PATTERNS['html'].items():
        print(f"\nTesting pattern: {pattern_name}")
        
        # Create and execute query
        query = parser.query(pattern)
        matches = query.matches(tree.root_node)
        
        print(f"Found {len(matches)} matches")
        
        # Print details of each match
        for i, match in enumerate(matches[:5]):  # Show first 5 matches
            print(f"\nMatch {i + 1}:")
            for capture_name, node in match[0].items():
                text = node.text.decode('utf8')
                if len(text) > 50:  # Truncate long text
                    text = text[:47] + "..."
                print(f"  {capture_name}: {text}")

if __name__ == '__main__':
    test_html_patterns() 