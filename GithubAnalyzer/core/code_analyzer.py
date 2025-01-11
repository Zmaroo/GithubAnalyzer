import os
from typing import List, Dict, Any, Optional, Union
from tree_sitter import Language, Parser
from GithubAnalyzer.core.models import TreeSitterNode, FunctionInfo, DocumentationInfo
from GithubAnalyzer.config.config import LANGUAGE_MAP, BINARY_EXTENSIONS, SKIP_PATHS
from GithubAnalyzer.core.tree_sitter_utils import get_tree_sitter_language, run_tree_sitter
from GithubAnalyzer.core.custom_parsers import parse_custom_file
from GithubAnalyzer.core.database_utils import Neo4jDatabase, PostgresDatabase
import traceback

class CodeAnalyzer:
    def __init__(self):
        """Initialize analyzer with database connections"""
        self.functions: Dict[str, FunctionInfo] = {}
        self.current_file = ""
        self.current_imports: List[str] = []
        self.all_functions: List[FunctionInfo] = []
        self.all_docs: List[DocumentationInfo] = []
        
        # Initialize database connections
        try:
            print("Initializing database connections...")
            self.neo4j_db = Neo4jDatabase()
            print("Neo4j connection initialized")
            self.postgres_db = PostgresDatabase()
            print("PostgreSQL connection initialized")
            print("Database connections initialized successfully")
        except Exception as e:
            print(f"Error initializing databases: {e}")
            traceback.print_exc()
            self.cleanup()
            raise
        
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'neo4j_db'):
                self.neo4j_db.close()
            if hasattr(self, 'postgres_db'):
                self.postgres_db.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            traceback.print_exc()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
    def should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed"""
        # Check skip paths
        if any(skip_path in file_path for skip_path in SKIP_PATHS):
            return False
            
        # Get file extension and name
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)
        
        # Skip binary files
        if ext in BINARY_EXTENSIONS:
            return False
            
        # Check if Tree-sitter supports this file
        if get_tree_sitter_language(ext) or get_tree_sitter_language(filename):
            return True
            
        # Check for custom parseable files
        if (filename.startswith('.env') or
            filename == 'requirements.txt' or
            filename.endswith('ignore') or
            ext in ['.properties', '.csv', '.tsv'] or
            filename.lower().startswith('license') or
            ext in ['.txt', '.text'] or
            filename in ['manifest.json', 'manifest.xml']):
            return True
            
        return False
    
    def _extract_imports(self, ast_root: TreeSitterNode, language: Language) -> List[str]:
        """Extract imports based on language"""
        imports = set()
        
        def visit_node(node: TreeSitterNode):
            # Get language type from extension
            ext = os.path.splitext(self.current_file)[1].lower()
            filename = os.path.basename(self.current_file)
            lang_type = LANGUAGE_MAP.get(ext.lower()) or LANGUAGE_MAP.get(filename)
            
            if not lang_type:
                return []
            
            # Python imports
            if lang_type == 'python':
                if node.type == 'import_statement':
                    name_nodes = [n for n in node.children if n.type == 'dotted_name']
                    for name_node in name_nodes:
                        if name_node.text:
                            imports.add(name_node.text.split('.')[0])
                elif node.type == 'import_from_statement':
                    module_nodes = [n for n in node.children if n.type == 'dotted_name']
                    if module_nodes:
                        imports.add(module_nodes[0].text.split('.')[0])
                        
            # JavaScript/TypeScript imports
            elif lang_type in ['javascript', 'typescript']:
                if node.type in ('import_statement', 'import_require_clause'):
                    source_nodes = [n for n in node.children if n.type == 'string']
                    if source_nodes:
                        package = source_nodes[0].text.strip('"\'')
                        if not package.startswith('.'):
                            package_name = package.split('/')[0]
                            if package_name.startswith('@'):
                                package_name = '/'.join(package.split('/')[:2])
                            imports.add(package_name)
                            
            # Java imports
            elif lang_type == 'java':
                if node.type == 'import_declaration':
                    name_nodes = [n for n in node.children if n.type == 'scoped_identifier']
                    if name_nodes:
                        imports.add(name_nodes[0].text.split('.')[0])
                        
            # Go imports
            elif lang_type == 'go':
                if node.type == 'import_spec':
                    path_nodes = [n for n in node.children if n.type == 'import_path']
                    if path_nodes:
                        imports.add(path_nodes[0].text.strip('"').split('/')[-1])
                        
            # Rust imports
            elif lang_type == 'rust':
                if node.type == 'use_declaration':
                    path_nodes = [n for n in node.children if n.type == 'scoped_identifier']
                    if path_nodes:
                        crate_name = path_nodes[0].text.split('::')[0]
                        if crate_name not in ('self', 'super', 'crate'):
                            imports.add(crate_name)
                            
            # PHP imports
            elif lang_type == 'php':
                if node.type in ('namespace_use_declaration', 'namespace_use_clause'):
                    name_nodes = [n for n in node.children if n.type == 'qualified_name']
                    if name_nodes:
                        imports.add(name_nodes[0].text.split('\\')[0])
                        
            # Ruby requires
            elif lang_type == 'ruby':
                if node.type == 'call' and node.children[0].text in ['require', 'require_relative']:
                    arg_nodes = [n for n in node.children if n.type == 'string']
                    if arg_nodes:
                        imports.add(arg_nodes[0].text.strip('"\''))
                        
            # Kotlin imports
            elif lang_type == 'kotlin':
                if node.type == 'import_header':
                    identifier_nodes = [n for n in node.children if n.type == 'identifier']
                    if identifier_nodes:
                        imports.add(identifier_nodes[0].text)
                        
            # Swift imports
            elif lang_type == 'swift':
                if node.type == 'import_declaration':
                    identifier_nodes = [n for n in node.children if n.type == 'identifier']
                    if identifier_nodes:
                        imports.add(identifier_nodes[0].text)
            
            # Recursively visit children
            for child in node.children:
                visit_node(child)
        
        visit_node(ast_root)
        return list(imports)
    
    def _create_function_info(self, node: TreeSitterNode, depth: int, language: str) -> Optional[FunctionInfo]:
        """Create FunctionInfo object from a function node"""
        try:
            # Extract function name
            name = ""
            if language == 'python':
                name_nodes = [n for n in node.children if n.type == 'identifier']
                if name_nodes:
                    name = name_nodes[0].text
            elif language in ['javascript', 'typescript']:
                name_nodes = [n for n in node.children if n.type in ['identifier', 'property_identifier']]
                if name_nodes:
                    name = name_nodes[0].text
            else:
                # Default name extraction for other languages
                name_nodes = [n for n in node.children if n.type in ['identifier', 'name', 'function_name']]
                if name_nodes:
                    name = name_nodes[0].text
            
            if not name:
                return None
            
            # Create function info
            func_info = FunctionInfo(
                name=name,
                file_path=self.current_file,
                imports=self.current_imports,
                nested_depth=depth
            )
            
            # Calculate metrics
            self._calculate_metrics(node, func_info, language)
            
            # Only return valid function info
            if func_info.name and func_info.file_path:
                return func_info
            return None
        except Exception as e:
            print(f"Error creating function info: {e}")
            traceback.print_exc()
            return None
    def analyze_tree_sitter_ast(self, ast_root: TreeSitterNode, language: str) -> Union[List[FunctionInfo], List[DocumentationInfo]]:
        """Analyze AST based on language"""
        # Get file extension
        ext = os.path.splitext(self.current_file)[1].lower()
        if ext == '.md':
            # For markdown files, only return documentation info
            return self.analyze_markdown_ast(ast_root)
        # For code files, only return function info
        return self.analyze_code_ast(ast_root, language)

    def analyze_code_ast(self, ast_root: TreeSitterNode, language: str) -> List[FunctionInfo]:
        """Analyze code AST to find functions"""
        # Skip markdown files
        if os.path.splitext(self.current_file)[1].lower() == '.md':
            return []
            
        functions = []
        
        def visit_node(node: TreeSitterNode, depth: int = 0):
            # Function definitions
            if node.type in [
                'function_definition',      # Python, C/C++
                'function_declaration',     # JavaScript
                'method_definition',        # JavaScript classes
                'function_item',           # Rust
                'method_declaration',      # Java
                'function_declaration',    # PHP
                'method',                  # Ruby
                'fun_declaration',         # Kotlin
                'function_declaration',    # Swift
                'func_declaration'         # Go
            ]:
                func_info = self._create_function_info(node, depth, language)
                if func_info:
                    functions.append(func_info)
            
            # Recursively visit children
            for child in node.children:
                visit_node(child, depth + (1 if node.type in ['class_definition', 'class_declaration'] else 0))
        
        visit_node(ast_root)
        return functions

    def analyze_markdown_ast(self, ast_root: TreeSitterNode) -> List[DocumentationInfo]:
        """Analyze markdown AST to extract documentation info"""
        title = ""
        section_headers = []
        content = ast_root.text.decode('utf-8') if isinstance(ast_root.text, bytes) else str(ast_root.text)

        def visit_node(node: TreeSitterNode):
            nonlocal title
            # Look for headings
            if node.type == 'atx_heading':
                # Extract heading text from inline node
                inline_nodes = [child for child in node.children if child.type == 'inline']
                if inline_nodes:
                    header_text = inline_nodes[0].text.decode('utf-8') if isinstance(inline_nodes[0].text, bytes) else str(inline_nodes[0].text)
                    header_text = header_text.strip()
                    if header_text:
                        if not title and node.start_point[0] == 0:  # First heading
                            title = header_text
                        section_headers.append(header_text)
            # Recursively visit children
            for child in node.children:
                visit_node(child)

        visit_node(ast_root)

        # If no title found in headings, use filename
        if not title:
            title = os.path.basename(self.current_file).replace('.md', '').replace('-', ' ').replace('_', ' ').title()

        # Create DocumentationInfo object
        doc_info = DocumentationInfo(
            file_path=self.current_file,
            content=content,
            doc_type='markdown',
            title=title,
            section_headers=section_headers
        )
        return [doc_info]
    
    def analyze_file(self, file_path: str) -> Union[List[FunctionInfo], List[DocumentationInfo]]:
        """Analyze a file using appropriate parser"""
        self.current_file = file_path
        
        # Ensure file exists and is readable
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist")
            return []
        if not os.access(file_path, os.R_OK):
            print(f"Error: File {file_path} is not readable")
            return []

        try:
            ext = os.path.splitext(file_path)[1].lower()
            # Read file content and normalize line endings
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                print(f"Warning: File {file_path} contains invalid UTF-8, trying with errors='replace'")
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            
            # Skip empty files
            if not content.strip():
                print(f"Warning: File {file_path} is empty")
                return []
            
            # Normalize line endings
            content = content.replace('\r\n', '\n')  # CRLF to LF
            content = content.replace('\r', '\n')    # CR to LF
            
            # Get appropriate parser
            ext = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path)
            print(f"Checking language for {file_path} (ext: {ext}, filename: {filename})")
            
            # Get appropriate language parser
            language = get_tree_sitter_language(ext) or get_tree_sitter_language(filename)
            if language:
                print(f"Found language: {language}")
            else:
                print(f"No language found for {ext}")
                
            if language:
                # Use Tree-sitter for supported languages
                print(f"Attempting to parse {file_path} ({language}) with tree-sitter")
                
                # Try direct parsing first
                print(f"Attempting parse of {file_path}")
                result = run_tree_sitter(content, language)
                if result["status"] != "success":
                    print(f"Failed to parse {file_path} with tree-sitter: {result.get('error')}")
                    # Fall back to custom parser
                    print(f"Falling back to custom parser for {file_path}")
                    result = parse_custom_file(file_path)
                    functions = self._analyze_custom_result(result)
                else:
                    print(f"Successfully parsed {file_path} with tree-sitter")
                    ast_root = result["root_node"]
                    
                    # Extract imports first (only for code files)
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext != '.md':
                        self.current_imports = self._extract_imports(ast_root, language)
                    
                    # Get language type from extension
                    filename = os.path.basename(file_path)
                    lang_type = LANGUAGE_MAP.get(ext.lower()) or LANGUAGE_MAP.get(filename)
                    
                    # Analyze structure based on language type
                    results = self.analyze_tree_sitter_ast(ast_root, lang_type or 'unknown')
                    # Add results to the appropriate collections
                    if ext == '.md':
                        self.all_docs.extend(results)
                        print(f"Found {len(results)} documentation files")
                    else:
                        self.all_functions.extend(results)
                        print(f"Found {len(results)} functions/methods")
                    return results
            else:
                # Use custom parser for other files
                result = parse_custom_file(file_path)
                functions = self._analyze_custom_result(result)
                self.all_functions.extend(functions)
                self._print_analysis_result(functions)
                return functions
        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            traceback.print_exc()
            return []
    
    def _print_analysis_result(self, result: Union[List[FunctionInfo], List[DocumentationInfo]]):
        """Print analysis result with correct count"""
        # Printing is now handled in analyze_tree_sitter_ast
        pass

    def store_all_functions(self, batch_size: int = 50):
        """Store all collected functions and documentation in both databases"""
        if not self.all_functions and not self.all_docs:
            print("No items to store")
            return
            
        print(f"\nStoring {len(self.all_functions)} functions and {len(self.all_docs)} documentation files...")
        try:
            # Store all items in both databases
            all_items = self.all_functions + self.all_docs
            if all_items:
                # PostgreSQL
                try:
                    self.postgres_db.store_functions(all_items, batch_size)
                except Exception as e:
                    print(f"Error storing items in PostgreSQL: {e}")
                    traceback.print_exc()
                
                # Neo4j
                try:
                    self.neo4j_db.store_functions(all_items, batch_size)
                except Exception as e:
                    print(f"Error storing items in Neo4j: {e}")
                    traceback.print_exc()
                    
            print("All items stored successfully")
        except Exception as e:
            print(f"Error storing items: {e}")
            traceback.print_exc()
            raise
    
    def _calculate_metrics(self, node: TreeSitterNode, func_info: FunctionInfo, language: str) -> None:
        """Calculate function metrics"""
        # Calculate cyclomatic complexity
        complexity = 1  # Base complexity
        
        def count_branches(n: TreeSitterNode) -> None:
            nonlocal complexity
            # Common branch types across languages
            branch_types = {
                'if_statement', 'else_clause',
                'for_statement', 'while_statement',
                'catch_clause', 'case_clause',
                'match_arm', 'when_expression'  # Rust/Kotlin pattern matching
            }
            if n.type in branch_types:
                complexity += 1
            for child in n.children:
                count_branches(child)
        
        count_branches(node)
        func_info.complexity = complexity
        
        # Calculate lines of code
        lines = set()
        
        def count_lines(n: TreeSitterNode) -> None:
            if n.start_point[0] is not None:
                lines.add(n.start_point[0])
            for child in n.children:
                count_lines(child)
        
        count_lines(node)
        func_info.lines_of_code = len(lines)
        
        # Set line numbers if available
        if node.start_point[0] is not None:
            func_info.start_line = node.start_point[0]
        if node.end_point[0] is not None:
            func_info.end_line = node.end_point[0]
    
    def _analyze_custom_result(self, result: Dict[str, Any]) -> Union[List[FunctionInfo], List[DocumentationInfo]]:
        """Create FunctionInfo objects from custom parser results"""
        functions = []
        
        if result["type"] == "environment":
            # Create a pseudo-function for environment variables
            func_info = FunctionInfo(
                name="environment_variables",
                file_path=self.current_file,
                docstring="Environment variable definitions",
                params=list(result["content"].keys())
            )
            functions.append(func_info)
            
        elif result["type"] == "requirements":
            # Create a pseudo-function for package requirements
            func_info = FunctionInfo(
                name="package_requirements",
                file_path=self.current_file,
                docstring="Package dependency definitions",
                params=list(result["content"].keys())
            )
            functions.append(func_info)
            
        elif result["type"] == "ignore":
            # Create a pseudo-function for ignore patterns
            func_info = FunctionInfo(
                name="ignore_patterns",
                file_path=self.current_file,
                docstring="File and directory ignore patterns",
                params=result["content"]
            )
            functions.append(func_info)
            
        elif result["type"] == "license":
            # Create a pseudo-function for license info
            func_info = FunctionInfo(
                name="license_info",
                file_path=self.current_file,
                docstring=f"Project license: {result['content']['type']}",
            )
            functions.append(func_info)
            
        return functions
