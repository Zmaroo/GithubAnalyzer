import os
from typing import Dict, Any, Optional, List
from tree_sitter import Language, Parser, Node
from ..config.config import LANGUAGE_MAP
from .models import TreeSitterNode
from .utils import setup_logger

logger = setup_logger(__name__)

def convert_node(node: Node) -> TreeSitterNode:
    """Convert a tree-sitter Node to our TreeSitterNode dataclass"""
    return TreeSitterNode(
        type=node.type,
        text=node.text.decode('utf-8') if isinstance(node.text, bytes) else str(node.text),
        start_point=node.start_point,
        end_point=node.end_point,
        children=[convert_node(child) for child in node.children]
    )

def get_tree_sitter_language(ext: str) -> Optional[Language]:
    """
    Get the appropriate Tree-sitter language for a file extension.
    Returns the Language object directly, not just the name.
    """
    try:
        # Check exact extension match
        lang_name = LANGUAGE_MAP.get(ext.lower())
        if lang_name:
            # Shell
            if lang_name == 'bash':
                import tree_sitter_bash as tsbash
                return Language(tsbash.language())
                
            # C/C++
            elif lang_name == 'c':
                import tree_sitter_c as tsc
                return Language(tsc.language())
            elif lang_name == 'cpp':
                import tree_sitter_cpp as tscpp
                return Language(tscpp.language())
                
            # Web Technologies
            elif lang_name == 'css':
                import tree_sitter_css as tscss
                return Language(tscss.language())
            elif lang_name == 'html':
                import tree_sitter_html as tshtml
                return Language(tshtml.language())
            elif lang_name == 'php':
                import tree_sitter_php as tsphp
                return Language(tsphp.language())
                
            # Programming Languages
            elif lang_name == 'go':
                import tree_sitter_go as tsgo
                return Language(tsgo.language())
            elif lang_name == 'java':
                import tree_sitter_java as tsjava
                return Language(tsjava.language())
            elif lang_name == 'javascript':
                import tree_sitter_javascript as tsjs
                return Language(tsjs.language())
            elif lang_name == 'typescript':
                try:
                    import tree_sitter_typescript
                    # Check if it's a TSX file
                    if ext.lower() == '.tsx':
                        return Language(tree_sitter_typescript.language_tsx())
                    # Regular TypeScript file
                    return Language(tree_sitter_typescript.language_typescript())
                except Exception as e:
                    print(f"Could not load TypeScript language: {e}")
                    # Fall back to JavaScript parser for TypeScript files
                    print("Falling back to JavaScript parser for TypeScript")
                    import tree_sitter_javascript as tsjs
                    return Language(tsjs.language())
            elif lang_name == 'kotlin':
                import tree_sitter_kotlin as tskotlin
                return Language(tskotlin.language())
            elif lang_name == 'scala':
                import tree_sitter_scala as tsscala
                return Language(tsscala.language())
            elif lang_name == 'ruby':
                import tree_sitter_ruby as tsruby
                return Language(tsruby.language())
            elif lang_name == 'python':
                import tree_sitter_python as tspython
                return Language(tspython.language())
            elif lang_name == 'rust':
                import tree_sitter_rust as tsrust
                return Language(tsrust.language())
            elif lang_name == 'lua':
                import tree_sitter_lua as tslua
                return Language(tslua.language())
                
            # Data & Config
            elif lang_name == 'json':
                import tree_sitter_json as tsjson
                return Language(tsjson.language())
            elif lang_name == 'yaml':
                import tree_sitter_yaml as tsyaml
                return Language(tsyaml.language())
            elif lang_name == 'toml':
                import tree_sitter_toml as tstoml
                return Language(tstoml.language())
            elif lang_name == 'xml':
                import tree_sitter_xml as tsxml
                return Language(tsxml.language())
                
            # Query Languages
            elif lang_name == 'sql':
                import tree_sitter_sql as tssql
                return Language(tssql.language())
                
            # Documentation
            elif lang_name == 'markdown':
                import tree_sitter_markdown as tsmarkdown
                return Language(tsmarkdown.language())
            
        # Check for files without extension
        filename = os.path.basename(ext)
        lang_name = LANGUAGE_MAP.get(filename)
        if lang_name:
            # Repeat the same language checks for files without extension
            if lang_name == 'bash':
                import tree_sitter_bash as tsbash
                return Language(tsbash.language())
            elif lang_name == 'c':
                import tree_sitter_c as tsc
                return Language(tsc.language())
            elif lang_name == 'cpp':
                import tree_sitter_cpp as tscpp
                return Language(tscpp.language())
            elif lang_name == 'css':
                import tree_sitter_css as tscss
                return Language(tscss.language())
            elif lang_name == 'html':
                import tree_sitter_html as tshtml
                return Language(tshtml.language())
            elif lang_name == 'php':
                import tree_sitter_php as tsphp
                return Language(tsphp.language())
            elif lang_name == 'go':
                import tree_sitter_go as tsgo
                return Language(tsgo.language())
            elif lang_name == 'java':
                import tree_sitter_java as tsjava
                return Language(tsjava.language())
            elif lang_name == 'javascript':
                import tree_sitter_javascript as tsjs
                return Language(tsjs.language())
            elif lang_name == 'typescript':
                try:
                    import tree_sitter_typescript
                    # Check if it's a TSX file
                    if ext.lower() == '.tsx':
                        return Language(tree_sitter_typescript.language_tsx())
                    # Regular TypeScript file
                    return Language(tree_sitter_typescript.language_typescript())
                except Exception as e:
                    print(f"Could not load TypeScript language: {e}")
                    # Fall back to JavaScript parser for TypeScript files
                    print("Falling back to JavaScript parser for TypeScript")
                    import tree_sitter_javascript as tsjs
                    return Language(tsjs.language())
            elif lang_name == 'kotlin':
                import tree_sitter_kotlin as tskotlin
                return Language(tskotlin.language())
            elif lang_name == 'scala':
                import tree_sitter_scala as tsscala
                return Language(tsscala.language())
            elif lang_name == 'ruby':
                import tree_sitter_ruby as tsruby
                return Language(tsruby.language())
            elif lang_name == 'python':
                import tree_sitter_python as tspython
                return Language(tspython.language())
            elif lang_name == 'rust':
                import tree_sitter_rust as tsrust
                return Language(tsrust.language())
            elif lang_name == 'lua':
                import tree_sitter_lua as tslua
                return Language(tslua.language())
            elif lang_name == 'json':
                import tree_sitter_json as tsjson
                return Language(tsjson.language())
            elif lang_name == 'yaml':
                import tree_sitter_yaml as tsyaml
                return Language(tsyaml.language())
            elif lang_name == 'toml':
                import tree_sitter_toml as tstoml
                return Language(tstoml.language())
            elif lang_name == 'xml':
                import tree_sitter_xml as tsxml
                return Language(tsxml.language())
            elif lang_name == 'sql':
                import tree_sitter_sql as tssql
                return Language(tssql.language())
            elif lang_name == 'markdown':
                import tree_sitter_markdown as tsmarkdown
                return Language(tsmarkdown.language())
        
        return None
    except Exception as e:
        print(f"Error getting language: {e}")
        return None

def run_tree_sitter(content: str, language: Language) -> Dict[str, Any]:
    """
    Run Tree-sitter parser on content with the specified language.
    Now accepts content directly instead of a file path.
    """
    parser = None
    try:
        # Skip empty content
        if not content.strip():
            return {
                "status": "error",
                "error": "Empty content"
            }
            
        # Create parser for this operation
        parser = Parser()
        parser.language = language
        
        # Parse the content
        tree = parser.parse(content.encode('utf8'))
        
        # Convert the root node to our TreeSitterNode type
        root_node = convert_node(tree.root_node)
        
        return {
            "status": "success",
            "tree": tree,
            "root_node": root_node
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {
            "status": "error",
            "error": f"Error parsing content: {e}"
        }
    finally:
        try:
            if 'tree' in locals():
                del tree
            if parser:
                # Clean up parser resources
                parser.reset()
                del parser
        except Exception as e:
            print(f"Error during cleanup: {e}")

def get_language_parser(language_name: str) -> Optional[Parser]:
    """Get a configured parser for a specific language"""
    try:
        # Get the language first
        if language_name == 'python':
            import tree_sitter_python
            language = Language(tree_sitter_python.language())
        else:
            logger.error(f"Language {language_name} not supported yet")
            return None
            
        # Create parser with language
        parser = Parser(language)  # Pass language directly to constructor
        
        return parser
        
    except Exception as e:
        logger.error(f"Error creating {language_name} parser: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
