import ast
import os
import git
from git import Repo
import networkx as nx
import tempfile
from typing import Dict, Any, List, Optional
from functools import wraps
import time
from datetime import datetime, date, timedelta
from ..core.database_utils import DatabaseManager
import logging
from ..core.tree_sitter_utils import get_tree_sitter_language, get_language_parser
import re
import redis
import pickle
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, backoff_factor: float = 2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        sleep_time = backoff_factor ** attempt
                        time.sleep(sleep_time)
            raise last_exception
        return wrapper
    return decorator

class ContextAnalyzer(ast.NodeVisitor):
    def __init__(self, target_line: int):
        self.target_line = target_line
        self.context = {
            'imports': [],
            'related_functions': [],
            'class_hierarchy': [],
            'usage_examples': [],
            'documentation': None
        }
        self.current_class = None

    def visit_Import(self, node):
        for name in node.names:
            self.context['imports'].append(name.name)

    def visit_ImportFrom(self, node):
        module = node.module or ''
        for name in node.names:
            self.context['imports'].append(f"{module}.{name.name}")

    def visit_ClassDef(self, node):
        if hasattr(node, 'lineno') and abs(node.lineno - self.target_line) < 50:
            class_info = {
                'name': node.name,
                'bases': [base.id for base in node.bases if isinstance(base, ast.Name)],
                'methods': []
            }
            self.context['class_hierarchy'].append(class_info)
        self.generic_visit(node)

    def get_context(self) -> Dict[str, Any]:
        return self.context

class AIAgentEnhanced:
    """
    Enhanced AI agent for deep code analysis and understanding.
    
    This class provides tools for AI models to:
    1. Analyze code structure and relationships
    2. Understand semantic patterns
    3. Visualize code relationships
    4. Query specific aspects of the codebase
    
    The tools are designed to be model-agnostic, allowing any AI model to:
    - Process code structure and relationships
    - Generate insights about code patterns
    - Make informed suggestions about code improvements
    - Understand project architecture
    """

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.codebase_understanding = None
        self.discovered_modules = []
        self.external_dependencies = []
        self.dependency_graph = nx.DiGraph()
        
        # Redis cache setup
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True  # For string data
            )
            self.binary_redis = redis.Redis(  # For binary data (embeddings)
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=False
            )
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            self.redis_client = None
            self.binary_redis = None
        
        self.context_cache = {}  # Fallback in-memory cache
        self._neo4j_session = None

    def __del__(self):
        """Ensure cleanup on object destruction"""
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        # Clear cache
        self._clear_cache()
        
        # Close Redis connections
        if hasattr(self, 'redis_client') and self.redis_client:
            self.redis_client.close()
        if hasattr(self, 'binary_redis') and self.binary_redis:
            self.binary_redis.close()
        
        # Close Neo4j session
        if self._neo4j_session:
            self._neo4j_session.close()
            self._neo4j_session = None
        
        # Close database connections
        if hasattr(self, 'db_manager'):
            self.db_manager.cleanup()

    def _get_neo4j_session(self):
        """Get or create a Neo4j session"""
        if not self._neo4j_session and self.db_manager.neo4j_driver:
            self._neo4j_session = self.db_manager.neo4j_driver.session()
        return self._neo4j_session

    def analyze_repo(self, repo_url: str, force_update: bool = False) -> Dict[str, Any]:
        """Analyze a repository and store results"""
        logger.info(f"Analyzing repository {repo_url}")
        try:
            repo_name = repo_url.split('/')[-1]
            
            # Check cache first if not forcing update
            if not force_update:
                cached_analysis = self._get_from_cache(repo_name, 'analysis')
                if cached_analysis:
                    logger.info(f"Using cached analysis for {repo_name}")
                    return cached_analysis

            local_path = os.path.join("./temp", repo_name)
            
            # Check if repo exists and needs update
            existing_repo = self.db_manager.get_repository_info(repo_name)
            if existing_repo and not force_update:
                update_check = self.check_repository_updates(repo_name)
                if not update_check.get('needs_update', False):
                    logger.info(f"Repository {repo_name} is up to date")
                    return existing_repo
                logger.info(f"Repository {repo_name} needs update: {update_check.get('reason')}")
            
            # Clone or update repository
            if os.path.exists(local_path):
                logger.info("Updating existing repository")
                repo = Repo(local_path)
                repo.remotes.origin.pull()
            else:
                logger.info("Cloning new repository")
                Repo.clone_from(repo_url, local_path)
            
            # Initialize analysis results
            analysis_results = {
                'name': repo_name,
                'url': repo_url,
                'local_path': local_path,
                'analysis': {}
            }
            
            # Analyze code structure
            code_analysis = self._analyze_project_structure(local_path)
            if code_analysis:
                analysis_results['analysis']['code'] = code_analysis
                
            # Analyze documentation
            doc_analysis = self.analyze_documentation(local_path)
            if doc_analysis:
                analysis_results['analysis']['documentation'] = doc_analysis
                
            # Serialize before storing
            serialized_results = self._serialize_analysis(analysis_results)
            
            # Store results in databases
            self.store_analysis_results(serialized_results)
            
            # Cache the results (already serialized)
            self._store_in_cache(repo_name, 'analysis', serialized_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _analyze_project_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze overall project structure"""
        try:
            analysis_results = {
                'modules': [],
                'dependencies': [],
                'structure': {}
            }
            
            for root, _, files in os.walk(repo_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if file in ['pyproject.toml', 'setup.py', 'requirements.txt']:
                        deps = self._analyze_dependencies(file_path)
                        if deps and isinstance(deps, list):
                            analysis_results['dependencies'].extend(deps)
                    elif file.endswith('.py'):
                        module_info = self._analyze_python_file(file_path)
                        if module_info and isinstance(module_info, dict):
                            # Add relative path instead of full path
                            module_info['path'] = os.path.relpath(file_path, repo_path)
                            # Make sure module_info has all required keys
                            if all(key in module_info for key in ['imports', 'functions', 'classes']):
                                analysis_results['modules'].append(module_info)
            
            # Add structure info
            analysis_results['structure'] = {
                'root': repo_path,
                'module_count': len(analysis_results['modules']),
                'dependency_count': len(analysis_results['dependencies'])
            }
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing project structure: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            module_info = {
                'path': file_path,
                'imports': [],
                'functions': [],
                'classes': [],
                'docstrings': []
            }
            
            # Parse with AST first for basic structure
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        module_info['imports'].append({
                            'name': name.name,
                            'asname': name.asname
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for name in node.names:
                        module_info['imports'].append({
                            'name': f"{module}.{name.name}",
                            'asname': name.asname
                        })
                elif isinstance(node, ast.FunctionDef):
                    module_info['functions'].append({
                        'name': node.name,
                        'lineno': node.lineno,
                        'args': [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    module_info['classes'].append({
                        'name': node.name,
                        'lineno': node.lineno,
                        'bases': [base.id for base in node.bases if isinstance(base, ast.Name)]
                    })
                    
            return module_info
            
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _cache_key(self, repo_name: str, category: str) -> str:
        """Generate consistent cache keys"""
        return f"{repo_name}:{category}"

    def _get_from_cache(self, repo_name: str, category: str) -> Optional[Any]:
        """Get data from cache (Redis or memory)"""
        if not self.redis_client:
            data = self.context_cache.get(f"{repo_name}:{category}")
            return self._deserialize_analysis(data) if data else None
            
        try:
            key = self._cache_key(repo_name, category)
            if category.endswith('_binary'):
                data = self.binary_redis.get(key)
                return pickle.loads(data) if data else None
            else:
                data = self.redis_client.get(key)
                if data:
                    return self._deserialize_analysis(json.loads(data))
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None

    def _store_in_cache(self, repo_name: str, category: str, data: Any, expire: int = 3600) -> bool:
        """Store data in cache with expiration"""
        if not self.redis_client:
            self.context_cache[f"{repo_name}:{category}"] = self._serialize_analysis(data)
            return True
            
        try:
            key = self._cache_key(repo_name, category)
            if category.endswith('_binary'):
                # Store binary data
                self.binary_redis.set(key, pickle.dumps(data), ex=expire)
            else:
                # Store JSON data
                serialized = self._serialize_analysis(data)
                self.redis_client.set(key, json.dumps(serialized), ex=expire)
            return True
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
            return False

    def _clear_cache(self, repo_name: str = None):
        """Clear cache for repository or all cache"""
        if not self.redis_client:
            if repo_name:
                keys_to_delete = [k for k in self.context_cache if k.startswith(f"{repo_name}:")]
                for k in keys_to_delete:
                    del self.context_cache[k]
            else:
                self.context_cache.clear()
            return

        try:
            pattern = f"{repo_name}:*" if repo_name else "*"
            for key in self.redis_client.scan_iter(pattern):
                self.redis_client.delete(key)
            if self.binary_redis:
                for key in self.binary_redis.scan_iter(pattern):
                    self.binary_redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")

    def _serialize_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize analysis data to JSON-compatible format"""
        try:
            # Handle special types
            if isinstance(data, dict):
                return {k: self._serialize_analysis(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [self._serialize_analysis(item) for item in data]
            elif isinstance(data, (datetime, date)):
                return data.isoformat()
            elif isinstance(data, nx.Graph):
                return {
                    'nodes': list(data.nodes()),
                    'edges': list(data.edges())
                }
            elif hasattr(data, '__dict__'):  # Custom objects
                return self._serialize_analysis(data.__dict__)
            return data
        except Exception as e:
            logger.warning(f"Serialization error: {e}")
            return str(data)  # Fallback to string representation

    def _deserialize_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize analysis data from JSON format"""
        try:
            if isinstance(data, dict):
                if 'nodes' in data and 'edges' in data:  # Graph reconstruction
                    G = nx.DiGraph()
                    G.add_nodes_from(data['nodes'])
                    G.add_edges_from(data['edges'])
                    return G
                return {k: self._deserialize_analysis(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [self._deserialize_analysis(item) for item in data]
            return data
        except Exception as e:
            logger.warning(f"Deserialization error: {e}")
            return data

    def _store_code_relationships(self, code_analysis: Dict[str, Any], repo_name: str) -> bool:
        """Store code relationships in Neo4j"""
        try:
            # Skip if Neo4j is not available
            if not self.db_manager.neo4j_driver:
                logger.warning("Neo4j not available - skipping relationship storage")
                return False

            session = self._get_neo4j_session()
            if not session:
                logger.warning("Could not create Neo4j session")
                return False

            # Create repository node
            session.run("""
                MERGE (r:Repository {name: $repo_name})
                SET r.last_analyzed = datetime()
            """, repo_name=repo_name)

            # Store modules and their relationships
            for module in code_analysis.get('modules', []):
                # Create module node
                session.run("""
                    MATCH (r:Repository {name: $repo_name})
                    MERGE (m:Module {path: $path})
                    MERGE (m)-[:BELONGS_TO]->(r)
                """, repo_name=repo_name, path=module['path'])

                # Store imports
                for imp in module.get('imports', []):
                    if isinstance(imp, dict):
                        import_name = imp.get('name')
                    else:
                        import_name = str(imp)
                    session.run("""
                        MATCH (m:Module {path: $path})
                        MERGE (i:Import {name: $import_name})
                        MERGE (m)-[:IMPORTS]->(i)
                    """, path=module['path'], import_name=import_name)

                # Store functions
                for func in module.get('functions', []):
                    if isinstance(func, dict):
                        func_name = func.get('name')
                        lineno = func.get('lineno')
                    else:
                        func_name = str(func)
                        lineno = None
                    session.run("""
                        MATCH (m:Module {path: $path})
                        MERGE (f:Function {name: $func_name, lineno: $lineno})
                        MERGE (f)-[:DEFINED_IN]->(m)
                    """, path=module['path'], func_name=func_name, lineno=lineno)

                # Store classes
                for cls in module.get('classes', []):
                    if isinstance(cls, dict):
                        class_name = cls.get('name')
                        bases = cls.get('bases', [])
                    else:
                        class_name = str(cls)
                        bases = []
                    session.run("""
                        MATCH (m:Module {path: $path})
                        MERGE (c:Class {name: $class_name})
                        MERGE (c)-[:DEFINED_IN]->(m)
                    """, path=module['path'], class_name=class_name)
                    
                    # Store inheritance relationships
                    for base in bases:
                        session.run("""
                            MATCH (c:Class {name: $class_name})
                            MERGE (b:Class {name: $base_name})
                            MERGE (c)-[:INHERITS_FROM]->(b)
                        """, class_name=class_name, base_name=base)

            return True

        except Exception as e:
            logger.error(f"Error storing code relationships: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def check_repository_updates(self, repo_name: str) -> Dict[str, Any]:
        """Check if repository needs updates"""
        try:
            # Get repository info from database
            repo_info = self.db_manager.get_repository_info(repo_name)
            if not repo_info:
                logger.warning(f"Repository {repo_name} not found in database")
                return {'needs_update': False, 'error': 'Repository not found'}

            local_path = os.path.join("./temp", repo_name)
            if not os.path.exists(local_path):
                return {'needs_update': True, 'reason': 'Local repository missing'}

            # Check git repository
            repo = Repo(local_path)
            try:
                # Fetch latest changes
                repo.remotes.origin.fetch()
                
                # Compare local and remote heads
                local_commit = repo.head.commit
                remote_commit = repo.remotes.origin.refs.master.commit
                
                if local_commit != remote_commit:
                    return {
                        'needs_update': True,
                        'reason': 'Remote changes available',
                        'local_commit': str(local_commit),
                        'remote_commit': str(remote_commit),
                        'last_analyzed': repo_info.get('last_analyzed')
                    }
                    
                # Check if analysis is outdated
                if repo_info.get('last_analyzed'):
                    last_analyzed = datetime.fromisoformat(repo_info['last_analyzed'])
                    if datetime.now() - last_analyzed > timedelta(days=7):
                        return {
                            'needs_update': True,
                            'reason': 'Analysis outdated',
                            'last_analyzed': repo_info['last_analyzed']
                        }
                        
                return {
                    'needs_update': False,
                    'last_analyzed': repo_info.get('last_analyzed')
                }
                
            except Exception as git_error:
                logger.error(f"Git error checking {repo_name}: {str(git_error)}")
                return {'needs_update': False, 'error': str(git_error)}
                
        except Exception as e:
            logger.error(f"Error checking updates for {repo_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'needs_update': False, 'error': str(e)}

    def analyze_documentation(self, repo_path: str) -> Dict[str, Any]:
        """Analyze repository documentation"""
        try:
            doc_analysis = {
                'readme': None,
                'api_docs': [],
                'docstrings': [],
                'comments': []
            }
            
            # Analyze README files
            readme_paths = ['README.md', 'README.rst', 'README.txt']
            for readme in readme_paths:
                path = os.path.join(repo_path, readme)
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        doc_analysis['readme'] = {
                            'content': f.read(),
                            'format': os.path.splitext(readme)[1][1:]
                        }
                    break
            
            # Analyze Python files for docstrings and comments
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Parse docstrings
                            tree = ast.parse(content)
                            docstring_visitor = DocstringVisitor()
                            docstring_visitor.visit(tree)
                            
                            if docstring_visitor.docstrings:
                                doc_analysis['docstrings'].append({
                                    'file': os.path.relpath(file_path, repo_path),
                                    'docstrings': docstring_visitor.docstrings
                                })
                            
                            # Extract comments
                            comments = self._extract_comments(content)
                            if comments:
                                doc_analysis['comments'].append({
                                    'file': os.path.relpath(file_path, repo_path),
                                    'comments': comments
                                })
                                
                        except Exception as e:
                            logger.warning(f"Error analyzing file {file_path}: {e}")
                            continue
            
            return doc_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing documentation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _extract_comments(self, content: str) -> List[Dict[str, Any]]:
        """Extract comments from Python code"""
        comments = []
        lines = content.split('\n')
        
        in_multiline = False
        multiline_content = []
        multiline_start = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Handle multiline comments
            if in_multiline:
                multiline_content.append(line)
                if '"""' in line or "'''" in line:
                    in_multiline = False
                    comments.append({
                        'type': 'multiline',
                        'content': '\n'.join(multiline_content),
                        'line_start': multiline_start,
                        'line_end': i
                    })
                continue
            
            # Start of multiline comment
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_multiline = True
                multiline_content = [line]
                multiline_start = i
                if stripped.endswith('"""') or stripped.endswith("'''"):
                    in_multiline = False
                    comments.append({
                        'type': 'multiline',
                        'content': line,
                        'line_start': i,
                        'line_end': i
                    })
                continue
            
            # Single line comments
            if '#' in line:
                comment_start = line.index('#')
                comment = line[comment_start:].strip()
                if comment != '#':  # Ignore empty comments
                    comments.append({
                        'type': 'inline',
                        'content': comment,
                        'line': i,
                        'column': comment_start
                    })
        
        return comments

    def store_analysis_results(self, analysis_results: Dict[str, Any]) -> bool:
        """Store analysis results in databases"""
        try:
            repo_name = analysis_results.get('name')
            if not repo_name:
                logger.error("No repository name in analysis results")
                return False

            # Store code relationships in Neo4j
            if 'analysis' in analysis_results and 'code' in analysis_results['analysis']:
                self._store_code_relationships(analysis_results['analysis']['code'], repo_name)

            # Store in PostgreSQL
            self.db_manager.store_repository_info(
                repo_name=repo_name,
                repo_url=analysis_results.get('url'),
                local_path=analysis_results.get('local_path'),
                analysis_data=analysis_results.get('analysis', {})
            )

            return True

        except Exception as e:
            logger.error(f"Error storing analysis results: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def get_stored_snippets_count(self, repo_name: str = None) -> int:
        """Get count of stored code snippets"""
        try:
            return self.db_manager.get_snippet_count(repo_name)
        except Exception as e:
            logger.error(f"Error getting snippet count: {e}")
            return 0

    def get_stored_relationships_count(self, repo_name: str = None) -> int:
        """Get count of stored code relationships"""
        try:
            if not self.db_manager.neo4j_driver:
                return 0
            
            with self._get_neo4j_session() as session:
                if repo_name:
                    result = session.run("""
                        MATCH (r:Repository {name: $repo_name})-[*]-(n)
                        RETURN count(*) as count
                    """, repo_name=repo_name)
                else:
                    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                return result.single()['count']
        except Exception as e:
            logger.error(f"Error getting relationship count: {e}")
            return 0

    def get_node_count(self, repo_name: str = None) -> int:
        """Get count of nodes in the code graph"""
        try:
            if not self.db_manager.neo4j_driver:
                return 0
            
            with self._get_neo4j_session() as session:
                if repo_name:
                    result = session.run("""
                        MATCH (r:Repository {name: $repo_name})-[*]-(n)
                        RETURN count(distinct n) as count
                    """, repo_name=repo_name)
                else:
                    result = session.run("MATCH (n) RETURN count(n) as count")
                return result.single()['count']
        except Exception as e:
            logger.error(f"Error getting node count: {e}")
            return 0

    def _analyze_dependencies(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze project dependencies from requirements or setup files"""
        try:
            dependencies = []
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('requirements.txt'):
                # Parse requirements.txt
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Handle version specifiers
                        parts = line.split('==')
                        if len(parts) == 2:
                            dependencies.append({
                                'name': parts[0],
                                'version': parts[1],
                                'type': 'requirement'
                            })
                        else:
                            dependencies.append({
                                'name': line,
                                'version': None,
                                'type': 'requirement'
                            })
                            
            elif file_path.endswith('setup.py'):
                # Basic setup.py parsing
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                        if node.func.id == 'setup':
                            for kw in node.keywords:
                                if kw.arg in ['install_requires', 'requires']:
                                    if isinstance(kw.value, ast.List):
                                        for elt in kw.value.elts:
                                            if isinstance(elt, ast.Str):
                                                dependencies.append({
                                                    'name': elt.s,
                                                    'type': 'setup'
                                                })
                                                
            elif file_path.endswith('pyproject.toml'):
                # Basic TOML parsing
                try:
                    import tomli
                    data = tomli.loads(content)
                    if 'project' in data and 'dependencies' in data['project']:
                        for dep in data['project']['dependencies']:
                            dependencies.append({
                                'name': dep,
                                'type': 'pyproject'
                            })
                except ImportError:
                    logger.warning("tomli not installed, skipping pyproject.toml parsing")
                    
            return dependencies
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies in {file_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

class DocstringVisitor(ast.NodeVisitor):
    """AST visitor for collecting docstrings"""
    def __init__(self):
        self.docstrings = []

    def visit_Module(self, node):
        if ast.get_docstring(node):
            self.docstrings.append({
                'type': 'module',
                'content': ast.get_docstring(node),
                'lineno': node.body[0].lineno if node.body else 0
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if ast.get_docstring(node):
            self.docstrings.append({
                'type': 'class',
                'name': node.name,
                'content': ast.get_docstring(node),
                'lineno': node.lineno
            })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if ast.get_docstring(node):
            self.docstrings.append({
                'type': 'function',
                'name': node.name,
                'content': ast.get_docstring(node),
                'lineno': node.lineno
            })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Handle async functions the same way as regular functions"""
        self.visit_FunctionDef(node)
