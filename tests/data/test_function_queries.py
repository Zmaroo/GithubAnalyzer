import json
import logging
import os
from pathlib import Path
from typing import List

from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.services.analysis.parsers.query_patterns import (
    JS_VARIANT_PATTERNS, QUERY_PATTERNS)
from GithubAnalyzer.services.analysis.parsers.traversal_service import \
    TreeSitterTraversal
from GithubAnalyzer.utils.logging import get_logger, get_tree_sitter_logger

# Get absolute path to workspace root and output directory
WORKSPACE_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
OUTPUT_DIR = WORKSPACE_ROOT / "@query_function_results"

# Initialize loggers
logger = get_logger("test_function_queries")
ts_logger = get_tree_sitter_logger()

# Set log levels to reduce noise
ts_logger.setLevel(logging.INFO)  # Show INFO level for tree-sitter
logger.setLevel(logging.INFO)     # Show INFO level for main logger

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
    "cs": "sample.cs",
    "rust": "sample.rs",
    "scala": "sample.scala",
    "ruby": "sample.rb",
    "swift": "sample.swift",
    "kotlin": "sample.kt",
    "lua": "sample.lua",
    "r": "sample.r",
    "dart": "sample.dart",
    
    # Newly added languages
    "groovy": "sample.groovy",
    "racket": "sample.rkt",
    "tcl": "sample.tcl",
    "verilog": "sample.sv",
    "zig": "sample.zig",
    "gleam": "sample.gleam",
    "hack": "sample.hack",
    "haxe": "sample.hx",
    "commonlisp": "sample.lisp",
    "clojure": "sample.clj",
    "ada": "sample.adb",
    "bash": "sample.sh",
    "elixir": "sample.ex",
    "erlang": "sample.erl",
    "haskell": "sample.hs",
    "purescript": "sample.purs",
    "julia": "sample.jl",
    "elm": "sample.elm",
    "gdscript": "sample.gd",
    "squirrel": "sample.nut",
    "solidity": "sample.sol",
    "php": "sample.php",
    "html": "sample.html",
    "powershell": "sample.ps1",
    "fish": "sample.fish"
}

def check_language_support(language_name: str) -> bool:
    """Check if a language has the required tree-sitter-language-pack support."""
    logger.info(f"Starting language support check for {language_name}")
    
    try:
        # Check binding
        logger.info(f"Checking binding for {language_name}")
        try:
            binding = get_binding(language_name)
            logger.info(f"Got binding for {language_name}")
        except Exception as e:
            logger.error(f"Failed to get binding for {language_name}: {str(e)}", extra={
                'context': {
                    'language': language_name,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'stage': 'binding'
                }
            })
            print(f"Binding error for {language_name}: {str(e)}")
            return False
        
        # Check language
        logger.info(f"Checking language for {language_name}")
        try:
            lang = get_language(language_name)
            logger.info(f"Got language for {language_name}")
        except Exception as e:
            logger.error(f"Failed to get language for {language_name}: {str(e)}", extra={
                'context': {
                    'language': language_name,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'stage': 'language'
                }
            })
            print(f"Language error for {language_name}: {str(e)}")
            return False
        
        # Check parser
        logger.info(f"Checking parser for {language_name}")
        try:
            parser = get_parser(language_name)
            logger.info(f"Got parser for {language_name}")
        except Exception as e:
            logger.error(f"Failed to get parser for {language_name}: {str(e)}", extra={
                'context': {
                    'language': language_name,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'stage': 'parser'
                }
            })
            print(f"Parser error for {language_name}: {str(e)}")
            return False
        
        logger.info(f"Successfully completed language support check for {language_name}")
        return True
    except Exception as e:
        logger.error(f"Language support check failed for {language_name}: {str(e)}", extra={
            'context': {
                'language': language_name,
                'error': str(e),
                'error_type': type(e).__name__,
                'stage': 'unknown'
            }
        })
        print(f"General error checking {language_name}: {str(e)}")
        return False

def process_language(language: str, pattern: str, file_path: Path):
    """Process a language file with a given pattern."""
    # Get the parser and language for the language
    parser = get_parser(language)
    lang = get_language(language)
    
    # Read and parse the file
    with open(file_path, 'r') as f:
        source = f.read()
    tree = parser.parse(bytes(source, 'utf8'))
    
    # Log successful parse
    logger.info(f"Successfully parsed {language} file")
    print(f"Successfully parsed {language} file")
    print(f"Root node type: {tree.root_node.type}")
    print(f"Number of child nodes: {len(tree.root_node.children)}")
    
    # Create and execute query
    logger.info(f"Creating query for {language}")
    print(f"Creating query for {language} with pattern:\n{pattern}\n")
    
    try:
        query = lang.query(pattern)  # Use language object to create query
        logger.info(f"Executing query for {language}")
        print(f"Executing query for {language}")
        matches = query.matches(tree.root_node)
        
        # Log query execution
        logger.info(f"Query executed for {language}", extra={
            'language': language,
            'pattern': pattern,
            'matches': len(matches)
        })
        print(f"Query execution completed for {language}. Found {len(matches)} matches.")
        
        # Process matches
        results = []
        for match in matches:
            match_info = {}
            for capture_name, node in match[1].items():
                # Handle both single nodes and lists of nodes
                if isinstance(node, list):
                    texts = [n.text.decode('utf8') for n in node]
                    match_info[str(capture_name)] = texts
                else:
                    text = node.text.decode('utf8')
                    match_info[str(capture_name)] = text
            results.append(match_info)
        
        # Write results to file
        output_dir = Path('@query_function_results')
        output_dir.mkdir(exist_ok=True)
        
        # For HTML, include the pattern name in the output file
        if language == "html":
            pattern_name = next((name for name, pat in QUERY_PATTERNS[language].items() if pat == pattern), "unknown")
            output_file = output_dir / f'{language}_{pattern_name}.json'
        else:
            output_file = output_dir / f'{language}_functions.json'
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Writing results for {language}", extra={
            'language': language,
            'output_file': str(output_file),
            'function_count': len(results)
        })
        print(f"Found {len(results)} matches in {language}")
        
        # Print sample of results
        for i, result in enumerate(results[:5]):
            print(f"\nMatch {i + 1}:")
            for capture_name, text in result.items():
                if isinstance(text, list):
                    print(f"  {capture_name}:")
                    for t in text[:3]:  # Show first 3 items if it's a list
                        print(f"    - {t[:100]}...")
                    if len(text) > 3:
                        print(f"    ... and {len(text) - 3} more")
                else:
                    print(f"  {capture_name}: {text[:100]}...")
            
    except Exception as e:
        logger.error(f"Query failed for {language}: {str(e)}", extra={
            'language': language,
            'pattern': pattern,
            'error': str(e),
            'error_type': type(e).__name__,
            'stage': 'query_execution'
        })
        print(f"Query failed for {language}: {str(e)}")

def main():
    # Process all languages that have patterns and sample files
    languages_to_test = {
        lang: SAMPLE_FILES[lang]
        for lang in QUERY_PATTERNS.keys()
        if lang in SAMPLE_FILES
    }
    
    print("\n=== Processing Languages ===\n")
    
    # Get the directory where this script is located
    current_dir = Path(__file__).parent
    
    print(f"Found {len(languages_to_test)} languages to process")
    print("\nWill process the following languages:")
    for lang in sorted(languages_to_test.keys()):
        print(f"  - {lang}")
    
    print("\n=== Beginning Analysis ===\n")
    
    for language_name, sample_file in sorted(languages_to_test.items()):
        sample_file = current_dir / sample_file
        print(f"\nProcessing {language_name} from {sample_file}...")
        try:
            # For HTML, process all patterns
            if language_name == "html":
                for pattern_name, pattern in QUERY_PATTERNS[language_name].items():
                    print(f"\nTesting pattern: {pattern_name}")
                    process_language(language_name, pattern, sample_file)
            # For other languages, just process the function pattern
            elif "function" in QUERY_PATTERNS[language_name]:
                process_language(language_name, QUERY_PATTERNS[language_name]["function"], sample_file)
        except Exception as e:
            print(f"Error processing {language_name}: {str(e)}")

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

def test_haxe_function_pattern():
    """Test that the Haxe function pattern correctly identifies functions."""
    language_name = "haxe"
    sample_file = Path(__file__).parent / SAMPLE_FILES[language_name]
    
    # Read the file
    with open(sample_file, 'rb') as f:
        code = f.read()
    
    # Get parser and language
    parser = get_parser(language_name)
    language = get_language(language_name)
    
    # Parse content
    tree = parser.parse(code)
    assert tree is not None, "Failed to parse Haxe file"
    
    # Get the pattern from query_patterns.py
    assert language_name in QUERY_PATTERNS, f"No patterns defined for {language_name}"
    assert "function" in QUERY_PATTERNS[language_name], f"No function pattern defined for {language_name}"
    
    query_pattern = QUERY_PATTERNS[language_name]["function"]
    query = language.query(query_pattern)
    
    # Execute query
    matches = query.matches(tree.root_node)
    assert len(matches) > 0, "No functions found in Haxe sample file"
    
    # Process matches
    functions = []
    for pattern_index, capture_dict in matches:
        for capture_name, nodes in capture_dict.items():
            for node in nodes:
                function_text = code[node.start_byte:node.end_byte].decode('utf8')
                functions.append({
                    "type": node.type,
                    "code": function_text
                })
    
    # Verify we found the expected function types
    function_types = set(f["type"] for f in functions)
    expected_types = {"function_declaration"}
    assert function_types.intersection(expected_types), f"Did not find expected function types. Found: {function_types}"

def test_hack_function_pattern():
    """Test that the Hack function pattern correctly identifies functions."""
    language_name = "hack"
    sample_file = Path(__file__).parent / SAMPLE_FILES[language_name]
    
    # Read the file
    with open(sample_file, 'rb') as f:
        code = f.read()
    
    # Get parser and language
    parser = get_parser(language_name)
    language = get_language(language_name)
    
    # Parse content
    tree = parser.parse(code)
    assert tree is not None, "Failed to parse Hack file"
    
    # Get the pattern from query_patterns.py
    assert language_name in QUERY_PATTERNS, f"No patterns defined for {language_name}"
    assert "function" in QUERY_PATTERNS[language_name], f"No function pattern defined for {language_name}"
    
    query_pattern = QUERY_PATTERNS[language_name]["function"]
    query = language.query(query_pattern)
    
    # Execute query
    matches = query.matches(tree.root_node)
    assert len(matches) > 0, "No functions found in Hack sample file"
    
    # Process matches
    functions = []
    for pattern_index, capture_dict in matches:
        for capture_name, nodes in capture_dict.items():
            for node in nodes:
                function_text = code[node.start_byte:node.end_byte].decode('utf8')
                functions.append({
                    "type": node.type,
                    "code": function_text
                })
    
    # Verify we found the expected function types
    function_types = set(f["type"] for f in functions)
    expected_types = {"method_declaration", "function_declaration", "constructor_declaration", "async_function_declaration", "lambda_expression"}
    assert function_types.intersection(expected_types), f"Did not find expected function types. Found: {function_types}"

def test_gleam_function_pattern():
    """Test that the Gleam function pattern correctly identifies functions."""
    language_name = "gleam"
    sample_file = Path(__file__).parent / SAMPLE_FILES[language_name]
    
    # Read the file
    with open(sample_file, 'rb') as f:
        code = f.read()
    
    # Get parser and language
    parser = get_parser(language_name)
    language = get_language(language_name)
    
    # Parse content
    tree = parser.parse(code)
    assert tree is not None, "Failed to parse Gleam file"
    
    # Get the pattern from query_patterns.py
    assert language_name in QUERY_PATTERNS, f"No patterns defined for {language_name}"
    assert "function" in QUERY_PATTERNS[language_name], f"No function pattern defined for {language_name}"
    
    query_pattern = QUERY_PATTERNS[language_name]["function"]
    query = language.query(query_pattern)
    
    # Execute query
    matches = query.matches(tree.root_node)
    assert len(matches) > 0, "No functions found in Gleam sample file"
    
    # Process matches
    functions = []
    for pattern_index, capture_dict in matches:
        for capture_name, nodes in capture_dict.items():
            for node in nodes:
                function_text = code[node.start_byte:node.end_byte].decode('utf8')
                functions.append({
                    "type": node.type,
                    "code": function_text
                })
    
    # Verify we found the expected function types
    function_types = set(f["type"] for f in functions)
    expected_types = {"function", "anonymous_function"}
    assert function_types.intersection(expected_types), f"Did not find expected function types. Found: {function_types}"

if __name__ == "__main__":
    # Process all languages that have patterns and sample files
    languages_to_test = {
        lang: SAMPLE_FILES[lang]
        for lang in QUERY_PATTERNS.keys()
        if lang in SAMPLE_FILES
    }
    
    print("\n=== Processing Languages ===\n")
    
    # Get the directory where this script is located
    current_dir = Path(__file__).parent
    
    print(f"Found {len(languages_to_test)} languages to process")
    print("\nWill process the following languages:")
    for lang in sorted(languages_to_test.keys()):
        print(f"  - {lang}")
    
    print("\n=== Beginning Analysis ===\n")
    
    for language_name, sample_file in sorted(languages_to_test.items()):
        sample_file = current_dir / sample_file
        print(f"\nProcessing {language_name} from {sample_file}...")
        try:
            # For HTML, process all patterns
            if language_name == "html":
                for pattern_name, pattern in QUERY_PATTERNS[language_name].items():
                    print(f"\nTesting pattern: {pattern_name}")
                    process_language(language_name, pattern, sample_file)
            # For other languages, just process the function pattern
            elif "function" in QUERY_PATTERNS[language_name]:
                process_language(language_name, QUERY_PATTERNS[language_name]["function"], sample_file)
        except Exception as e:
            print(f"Error processing {language_name}: {str(e)}") 