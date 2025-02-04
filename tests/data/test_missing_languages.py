from tree_sitter_language_pack import get_binding, get_language, get_parser
import logging
from pathlib import Path
from src.GithubAnalyzer.services.analysis.parsers.query_patterns import QUERY_PATTERNS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("language_test")

def test_language_support(name, sample_file_path):
    """Test tree-sitter support for a language with detailed error reporting."""
    print(f"\n=== Testing {name} ===")
    
    # Test binding
    try:
        binding = get_binding(name)
        print(f"✓ Got binding for {name}")
    except Exception as e:
        print(f"✗ Failed to get binding for {name}: {str(e)}")
        return False
        
    # Test language
    try:
        lang = get_language(name)
        print(f"✓ Got language for {name}")
    except Exception as e:
        print(f"✗ Failed to get language for {name}: {str(e)}")
        return False
        
    # Test parser
    try:
        parser = get_parser(name)
        print(f"✓ Got parser for {name}")
    except Exception as e:
        print(f"✗ Failed to get parser for {name}: {str(e)}")
        return False
        
    # Test parsing sample file
    try:
        with open(sample_file_path, 'rb') as f:
            code = f.read()
        print(f"✓ Read sample file: {sample_file_path}")
        
        tree = parser.parse(code)
        if tree and tree.root_node:
            print(f"✓ Successfully parsed {name} file")
            print(f"  Root node type: {tree.root_node.type}")
            print(f"  Number of child nodes: {len(tree.root_node.children)}")
            
            # Test query pattern
            try:
                if name not in QUERY_PATTERNS or "function" not in QUERY_PATTERNS[name]:
                    print(f"✗ No query pattern defined for {name}")
                    return False
                    
                query_pattern = QUERY_PATTERNS[name]["function"]
                print(f"\nTesting query pattern for {name}:")
                print(query_pattern)
                
                query = lang.query(query_pattern)
                matches = query.matches(tree.root_node)
                print(f"\n✓ Query executed successfully")
                print(f"Found {len(matches)} function matches")
                
                # Print first few matches
                for i, (pattern_index, capture_dict) in enumerate(matches[:3]):
                    for name, nodes in capture_dict.items():
                        if not isinstance(nodes, list):
                            nodes = [nodes]
                        for node in nodes:
                            text = code[node.start_byte:node.end_byte].decode('utf8')
                            print(f"\nMatch {i+1}:")
                            print(f"  Type: {node.type}")
                            print(f"  Text: {text[:100]}...")
                
                if len(matches) > 3:
                    print(f"\n... and {len(matches) - 3} more matches")
                
            except Exception as e:
                print(f"✗ Failed to execute query for {name}: {str(e)}")
                return False
                
            return True
        else:
            print(f"✗ Failed to parse {name} file - no valid tree produced")
            return False
    except Exception as e:
        print(f"✗ Error parsing {name} file: {str(e)}")
        return False

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

print("\nTesting language support with sample files...")
for lang, sample_file in languages_to_test.items():
    sample_path = WORKSPACE_ROOT / "tests" / "data" / sample_file
    test_language_support(lang, sample_path) 