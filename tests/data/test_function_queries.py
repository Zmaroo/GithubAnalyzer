from tree_sitter_language_pack import get_binding, get_language, get_parser
import json
from pathlib import Path
import os
from GithubAnalyzer.services.analysis.parsers.traversal_service import TreeSitterTraversal
from GithubAnalyzer.utils.logging import get_logger, get_tree_sitter_logger
import logging
from typing import List

# Get absolute path to workspace root and output directory
WORKSPACE_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
OUTPUT_DIR = WORKSPACE_ROOT / "@query_function_results"

# Initialize loggers
logger = get_logger("test_function_queries")
ts_logger = get_tree_sitter_logger()

# Set log levels to reduce noise
ts_logger.setLevel(logging.ERROR)  # Only show ERROR level for tree-sitter
logger.setLevel(logging.ERROR)     # Only show ERROR level for main logger

# Sample files for each language
SAMPLE_FILES = {
    # Original languages
    "python": "sample_types.py",
    "javascript": "app.js",
    "typescript": "types.ts",
    "go": "server.go",
    "java": "Service.java",
    "c": "sample.c",
    "cpp": "sample.cpp",
    "rust": "sample.rs",
    "scala": "sample.scala",
    "ruby": "sample.rb",
    "swift": "sample.swift",
    "kotlin": "sample.kt",
    "lua": "sample.lua",
    "r": "sample.r",
    
    # Newly added languages
    "groovy": "sample.groovy",
    "racket": "sample.rkt",
    "tcl": "sample.tcl",
    "verilog": "sample.v",
    "zig": "sample.zig",
    "gleam": "sample.gleam",
    "hack": "sample.hack",
    "haxe": "sample.hx",
    "ocaml": "sample.ml",
    "commonlisp": "sample.lisp",
    "clojure": "sample.clj",
    "ada": "sample.adb",
    "bash": "sample.sh",
    "elixir": "sample.ex",
    "erlang": "sample.erl",
    "haskell": "sample.hs",
    "purescript": "sample.purs"
}

def process_language(language_name: str, query_pattern: str, sample_file: Path):
    """Process a single language and output its function query results."""
    if not sample_file.exists():
        logger.error(f"Sample file for {language_name} not found: {sample_file}")
        return
        
    print(f"\nActual pattern being used for {language_name}:")
    print(query_pattern)
    
    # Initialize parser
    parser = get_parser(language_name)
    language = get_language(language_name)
    
    # Set up logging callback
    def logger_callback(log_type: int, msg: str) -> None:
        if log_type == 1:  # Only log errors
            ts_logger.error(msg, extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'parser',
                    'language': language_name,
                    'log_type': 'error'
                }
            })
    
    # Set the logger on the parser
    parser.logger = logger_callback
    
    # Read file content
    with open(sample_file, 'rb') as f:
        code = f.read()
    
    logger.info(f"Parsing {language_name} file", extra={
        'context': {
            'file': str(sample_file),
            'language': language_name,
            'content_size': len(code)
        }
    })
    
    # Parse content
    tree = parser.parse(code)
    
    if tree is None:
        logger.error(f"Failed to parse {language_name} file", extra={
            'context': {
                'file': str(sample_file),
                'language': language_name
            }
        })
        return
        
    logger.info(f"Successfully parsed {language_name} file", extra={
        'context': {
            'file': str(sample_file),
            'language': language_name,
            'has_error': tree.root_node.has_error
        }
    })
    
    # Create and execute query
    try:
        # Get the pattern from query_patterns.py
        from GithubAnalyzer.services.analysis.parsers.query_patterns import QUERY_PATTERNS
        if language_name in QUERY_PATTERNS and "function" in QUERY_PATTERNS[language_name]:
            query_pattern = QUERY_PATTERNS[language_name]["function"]
        
        query = language.query(query_pattern)
        matches = query.matches(tree.root_node)
        
        logger.info(f"Query executed for {language_name}", extra={
            'context': {
                'language': language_name,
                'matches': len(matches),
                'pattern': query_pattern
            }
        })
    except Exception as e:
        logger.error(f"Query failed for {language_name}: {str(e)}", extra={
            'context': {
                'language': language_name,
                'pattern': query_pattern,
                'error': str(e)
            }
        })
        raise
    
    # Process matches
    functions = []
    
    for pattern_index, capture_dict in matches:
        for capture_name, nodes in capture_dict.items():
            for node in nodes:
                # Get function text
                function_text = code[node.start_byte:node.end_byte].decode('utf8')
                
                # Get function details
                function_info = {
                    "type": node.type,
                    "start_point": {"row": node.start_point[0], "column": node.start_point[1]},
                    "end_point": {"row": node.end_point[0], "column": node.end_point[1]},
                    "code": function_text,
                    "name": "Anonymous"  # Default name
                }
                
                # Try to get function name if available
                name_node = node.child_by_field_name("name")
                if name_node:
                    function_info["name"] = code[name_node.start_byte:name_node.end_byte].decode('utf8')
                
                functions.append(function_info)
    
    # Write results to file
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / f"{language_name}_functions.json"
    logger.info(f"Writing results for {language_name}", extra={
        'context': {
            'language': language_name,
            'output_file': str(output_file),
            'function_count': len(functions)
        }
    })
    
    with open(output_file, 'w') as f:
        json.dump({
            "language": language_name,
            "pattern": query_pattern,
            "total_functions": len(functions),
            "functions": functions
        }, f, indent=2)
    
    print(f"Found {len(functions)} functions in {language_name}")
    for func in functions:
        name = func.get("name", "anonymous")
        print(f"  - {name} ({func['type']})")
        print(f"    Code: {func['code'][:100]}...")  # Print first 100 chars of code

def main():
    from GithubAnalyzer.services.analysis.parsers.query_patterns import QUERY_PATTERNS, JS_VARIANT_PATTERNS
    
    # First, print debug information about available languages and patterns
    print("\n=== Language Support Analysis ===")
    print("\nLanguages in QUERY_PATTERNS:")
    for lang in sorted(QUERY_PATTERNS.keys()):
        has_pattern = 'function' in QUERY_PATTERNS[lang]
        has_sample = lang in SAMPLE_FILES
        print(f"  - {lang:<15} {'✓' if has_pattern else '✗'} pattern {'✓' if has_sample else '✗'} sample")
    
    # Filter languages that have both patterns and sample files
    languages_to_test = {
        lang: SAMPLE_FILES[lang]
        for lang in QUERY_PATTERNS.keys()
        if "function" in QUERY_PATTERNS[lang] and lang in SAMPLE_FILES
    }

    print(f"\nFound {len(languages_to_test)} languages with both patterns and sample files")
    print("\nWill test the following languages:")
    for lang in sorted(languages_to_test.keys()):
        print(f"  - {lang}")
    
    print("\n=== Beginning Analysis ===\n")
    
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Process each language
    for language_name, patterns in {**QUERY_PATTERNS, **JS_VARIANT_PATTERNS}.items():
        if "function" not in patterns:
            print(f"Skipping {language_name}: no function pattern defined")
            continue
            
        sample_file = Path("tests/data") / SAMPLE_FILES.get(language_name, f"sample.{language_name}")
        if sample_file.exists():
            print(f"\nProcessing {language_name}...")
            try:
                process_language(language_name, patterns["function"], sample_file)
            except Exception as e:
                print(f"Error processing {language_name}: {str(e)}")
        else:
            print(f"Skipping {language_name}: sample file not found at {sample_file}")

def analyze_ast_nodes(lang: str, sample_file: str):
    """Analyze AST nodes using advanced Tree-sitter features."""
    print(f"\nDetailed AST analysis for {lang}...")
    
    # Get parser and language
    parser = get_parser(lang)
    language = get_language(lang)
    
    # Read and parse file
    with open(sample_file, 'rb') as f:
        code = f.read()
        tree = parser.parse(code)
    
    # Create query from the pattern
    from GithubAnalyzer.services.analysis.parsers.query_patterns import QUERY_PATTERNS
    pattern = QUERY_PATTERNS[lang]["function"]
    query = language.query(pattern)
    
    print(f"\nAnalyzing node types in {lang}:")
    
    # Track unique node types and their properties
    node_types = {}
    
    # Process matches - returns list of (pattern_index, capture_dict) tuples
    matches = query.matches(tree.root_node)
    print(f"Matches type: {type(matches)}")  # Debug print
    print(f"Number of matches: {len(matches)}")  # Debug print
    
    # Handle matches following test_ts_functions.py pattern
    for pattern_index, capture_dict in matches:
        for capture_name, nodes in capture_dict.items():
            if not isinstance(nodes, list):
                nodes = [nodes]
                
            for node in nodes:
                # Print capture details
                print(f"\nFound {capture_name} (pattern {pattern_index}):")
                print(f"  Node type: {node.type}")
                text = code[node.start_byte:node.end_byte].decode('utf8')
                print(f"  Text: {text[:60]}...")
                
                # Print field names if any
                try:
                    # Get field names first
                    field_names = list(node.children_by_field_name.keys())
                    if field_names:
                        print("  Fields:")
                        for field_name in field_names:
                            field_node = node.child_by_field_name(field_name)
                            if field_node:
                                field_text = code[field_node.start_byte:field_node.end_byte].decode('utf8')
                                print(f"    {field_name}: {field_node.type} = {field_text[:40]}...")
                except (AttributeError, TypeError):
                    pass  # Node doesn't have field names
                
                # Print children if any
                if len(node.children) > 0:
                    print("  Children:")
                    for child in node.children:
                        child_text = code[child.start_byte:child.end_byte].decode('utf8')
                        print(f"    {child.type} = {child_text[:40]}...")
                
                # Track node type info
                if node.type not in node_types:
                    node_id = language.id_for_node_kind(node.type, True)
                    node_types[node.type] = {
                        "is_named": language.node_kind_is_named(node_id),
                        "is_visible": language.node_kind_is_visible(node_id),
                        "is_supertype": language.node_kind_is_supertype(node_id),
                        "capture_names": set(),
                        "count": 0
                    }
                
                node_types[node.type]["capture_names"].add(capture_name)
                node_types[node.type]["count"] += 1
    
    # Print summary
    print(f"\nSummary for {lang}:")
    for node_type, info in node_types.items():
        print(f"\nNode type: {node_type}")
        print(f"  Named: {info['is_named']}")
        print(f"  Visible: {info['is_visible']}")
        print(f"  Supertype: {info['is_supertype']}")
        print(f"  Captures: {', '.join(info['capture_names'])}")
        print(f"  Count: {info['count']}")

def print_language_node_types(lang: str):
    """Print all available node types for a language."""
    language = get_language(lang)
    
    # Get all node types
    node_types = set()
    for i in range(language.node_kind_count()):
        name = language.node_kind_for_id(i)
        if name and language.node_kind_is_named(i):
            node_types.add(name)
    
    print(f"\nAvailable node types for {lang}:")
    for node_type in sorted(node_types):
        print(f"  - {node_type}")

def get_all_node_types(sample_file: str):
    """Get all node types from a sample file."""
    # Get language from file extension
    ext = os.path.splitext(sample_file)[1][1:]  # Remove the dot
    lang = next((lang for lang, file in SAMPLE_FILES.items() if file.endswith(ext)), None)
    if not lang:
        raise ValueError(f"Could not determine language for file: {sample_file}")
    
    parser = get_parser(lang)
    traversal = TreeSitterTraversal()
    
    # Read and parse file
    with open(sample_file, 'rb') as f:
        tree = parser.parse(f.read())
    
    # Collect all unique node types
    node_types = set()
    for node in traversal.walk_tree(tree.root_node):
        if node.is_named:
            node_types.add(node.type)
    
    return sorted(node_types)

def analyze_all_languages():
    """Analyze AST nodes for all languages that have function patterns."""
    # Set up logging
    logger = logging.getLogger("test_function_queries")
    ts_logger = logging.getLogger("tree_sitter")
    logger.setLevel(logging.INFO)
    ts_logger.setLevel(logging.INFO)

    # Get all languages that have function patterns
    from GithubAnalyzer.services.analysis.parsers.query_patterns import QUERY_PATTERNS
    
    # First, print debug information about available languages and patterns
    print("\n=== Language Support Analysis ===")
    print("\nLanguages in QUERY_PATTERNS:")
    for lang in sorted(QUERY_PATTERNS.keys()):
        has_pattern = 'function' in QUERY_PATTERNS[lang]
        has_sample = lang in SAMPLE_FILES
        print(f"  - {lang:<15} {'✓' if has_pattern else '✗'} pattern {'✓' if has_sample else '✗'} sample")
    
    # Filter languages that have both patterns and sample files
    languages_to_test = {
        lang: SAMPLE_FILES[lang]
        for lang in QUERY_PATTERNS.keys()
        if "function" in QUERY_PATTERNS[lang] and lang in SAMPLE_FILES
    }

    print(f"\nFound {len(languages_to_test)} languages with both patterns and sample files")
    print("\nWill test the following languages:")
    for lang in sorted(languages_to_test.keys()):
        print(f"  - {lang}")
    
    print("\n=== Beginning Analysis ===\n")

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    # Now proceed with testing each language
    for lang, sample_file in sorted(languages_to_test.items()):
        file_path = Path(os.path.join(os.path.dirname(__file__), sample_file))
        if not file_path.exists():
            print(f"\nSkipping {lang} - sample file not found: {sample_file}")
            continue
            
        print(f"\nAnalyzing {lang}...")
        try:
            # First process the language to generate output files
            process_language(lang, QUERY_PATTERNS[lang]["function"], file_path)
            
            # Then do detailed AST analysis
            print(f"\nAvailable node types in {lang}:")
            for node_type in get_all_node_types(str(file_path)):
                print(f"  - {node_type}")
            
            analyze_ast_nodes(lang, str(file_path))
        except Exception as e:
            print(f"Error analyzing {lang}: {str(e)}")

def analyze_specific_languages(languages: List[str]):
    """Analyze AST nodes for specific languages."""
    for lang in languages:
        print(f"\nAnalyzing {lang}...")
        if lang not in SAMPLE_FILES:
            print(f"No sample file defined for {lang}")
            continue
            
        file_path = Path(SAMPLE_FILES[lang])
        if not file_path.exists():
            print(f"Sample file not found at {file_path}")
            continue
            
        try:
            nodes = get_all_node_types(str(file_path))
            print(f"Found node types for {lang}:")
            for node_type, count in nodes.items():
                print(f"  - {node_type}: {count}")
        except Exception as e:
            print(f"Error analyzing {lang}: {e}")

if __name__ == "__main__":
    from GithubAnalyzer.services.analysis.parsers.query_patterns import QUERY_PATTERNS
    
    # Only test the 3 supported languages
    languages_to_test = {
        lang: SAMPLE_FILES[lang]
        for lang in ['hack', 'gleam', 'haxe']
    }

    print("\n=== Testing New Language Patterns ===")
    print("\nTesting the following languages:")
    for lang in sorted(languages_to_test.keys()):
        print(f"  - {lang}")
    
    print("\n=== Beginning Analysis ===\n")

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Process each language
    for lang, sample_file in sorted(languages_to_test.items()):
        file_path = Path(os.path.join(os.path.dirname(__file__), sample_file))
        if not file_path.exists():
            print(f"\nSkipping {lang} - sample file not found: {sample_file}")
            continue
            
        print(f"\nProcessing {lang}...")
        try:
            # First get all node types to see what's available
            nodes = get_all_node_types(str(file_path))
            print(f"\nAvailable node types in {lang}:")
            for node in nodes:
                print(f"  - {node}")
                
            # Then process the language
            process_language(lang, QUERY_PATTERNS[lang]["function"], file_path)
        except Exception as e:
            print(f"Error processing {lang}: {str(e)}") 