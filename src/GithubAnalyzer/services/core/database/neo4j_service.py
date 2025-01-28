from neo4j import GraphDatabase

from GithubAnalyzer.services.core.database.db_config import get_neo4j_config
from typing import Optional, List, Dict, Any

class Neo4jService:
    def __init__(self):
        self._driver = None
        self._config = get_neo4j_config()

    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self._config["uri"],
                auth=(self._config["username"], self._config["password"])
            )

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._driver:
            self._driver.close()
            self._driver = None

    def setup_constraints(self) -> None:
        """Setup necessary constraints for the graph database."""
        with self._driver.session() as session:
            # Create constraints for unique identifiers
            session.run("""
                CREATE CONSTRAINT file_path IF NOT EXISTS
                FOR (f:File) REQUIRE f.path IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT function_id IF NOT EXISTS
                FOR (fn:Function) REQUIRE fn.id IS UNIQUE
            """)

    def create_file_node(self, repo_id: int, file_path: str) -> None:
        """Create a file node in the graph.
        
        Args:
            repo_id: Repository identifier (integer)
            file_path: Path to the file
        """
        with self._driver.session() as session:
            session.run("""
                MERGE (f:File {path: $path})
                SET f.repo_id = $repo_id
            """, path=file_path, repo_id=repo_id)

    def create_function_node(self, repo_id: int, file_path: str, name: str) -> None:
        """Create a function node in the graph.
        
        Args:
            repo_id: Repository identifier (integer)
            file_path: Path to the file containing the function
            name: Function name
        """
        with self._driver.session() as session:
            session.run("""
                MATCH (f:File {path: $path})
                MERGE (fn:Function {id: $path + '/' + $name})
                ON CREATE SET fn.name = $name, fn.repo_id = $repo_id
                MERGE (fn)-[:DEFINED_IN]->(f)
            """, path=file_path, name=name, repo_id=repo_id)

    def create_class_node(self, repo_id: int, file_path: str, name: str) -> None:
        """Create a class node in the graph.
        
        Args:
            repo_id: Repository identifier (integer)
            file_path: Path to the file containing the class
            name: Class name
        """
        with self._driver.session() as session:
            session.run("""
                MATCH (f:File {path: $path})
                MERGE (c:Class {id: $path + '/' + $name})
                ON CREATE SET c.name = $name, c.repo_id = $repo_id
                MERGE (c)-[:DEFINED_IN]->(f)
            """, path=file_path, name=name, repo_id=repo_id)

    def create_import_relationship(self, repo_id: int, file_path: str, module_name: str) -> None:
        """Create an import relationship in the graph.
        
        Args:
            repo_id: Repository identifier (integer)
            file_path: Path to the file containing the import
            module_name: Name of the imported module
        """
        with self._driver.session() as session:
            session.run("""
                MATCH (f:File {path: $path})
                MERGE (m:Module {name: $module_name})
                ON CREATE SET m.repo_id = $repo_id
                MERGE (f)-[:IMPORTS]->(m)
            """, path=file_path, module_name=module_name, repo_id=repo_id)

    def create_function_relationship(self, caller_path: str, callee_path: str,
                                   caller_name: str, callee_name: str) -> None:
        """Create a relationship between functions in different files."""
        with self._driver.session() as session:
            # First, create the function nodes and their relationships to files
            session.run("""
                MATCH (f1:File {path: $caller_path})
                MERGE (fn1:Function {id: $caller_path + '/' + $caller_name})
                ON CREATE SET fn1.name = $caller_name
                MERGE (fn1)-[:DEFINED_IN]->(f1)
            """, caller_path=caller_path, caller_name=caller_name)

            session.run("""
                MATCH (f2:File {path: $callee_path})
                MERGE (fn2:Function {id: $callee_path + '/' + $callee_name})
                ON CREATE SET fn2.name = $callee_name
                MERGE (fn2)-[:DEFINED_IN]->(f2)
            """, callee_path=callee_path, callee_name=callee_name)

            # Then create the CALLS relationship between functions
            session.run("""
                MATCH (fn1:Function {id: $caller_path + '/' + $caller_name})
                MATCH (fn2:Function {id: $callee_path + '/' + $callee_name})
                MERGE (fn1)-[:CALLS]->(fn2)
            """, caller_path=caller_path, callee_path=callee_path,
                 caller_name=caller_name, callee_name=callee_name)

    def get_file_relationships(self, file_path: str) -> List[Dict[str, Any]]:
        """Get function relationships for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of function relationships
        """
        with self._driver.session() as session:
            result = session.run('''
                MATCH (f:File {path: $path})<-[:DEFINED_IN]-(fn:Function)
                OPTIONAL MATCH (fn)-[r:CALLS]->(called:Function)-[:DEFINED_IN]->(cf:File)
                RETURN fn.name as function_name,
                       collect({
                           function: called.name,
                           file: cf.path
                       }) as calls
            ''', path=file_path)
            
            return [
                {
                    'function': record['function_name'],
                    'calls': record['calls']
                }
                for record in result
            ]

    def get_function_callers(self, function_name: str) -> List[Dict[str, Any]]:
        """Get all functions that call a specific function.
        
        Args:
            function_name: Name of the function
            
        Returns:
            List of dictionaries containing caller information
        """
        with self._driver.session() as session:
            result = session.run("""
                MATCH (caller:Function)-[r:CALLS]->(called:Function {name: $name})
                MATCH (caller)<-[:CONTAINS]-(cf:File)
                RETURN cf.path as file,
                       caller.name as function
            """, name=function_name)
            
            return [dict(record) for record in result]

    def find_similar_repos(self, repo_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find repositories with similar code patterns and structures.
        
        Uses GDS node similarity algorithms to find repos with similar:
        - Function patterns
        - Import relationships
        - Code organization
        
        Args:
            repo_id: Repository ID to find similar repos for
            limit: Maximum number of results
        """
        with self._driver.session() as session:
            # First, create a graph projection for the repository structures
            session.run("""
                CALL gds.graph.project(
                    'repo_structure',
                    ['Repository', 'File', 'Function', 'Class'],
                    {
                        CONTAINS: {orientation: 'UNDIRECTED'},
                        CALLS: {orientation: 'UNDIRECTED'},
                        IMPORTS: {orientation: 'UNDIRECTED'}
                    }
                )
            """)
            
            # Run node similarity to find similar repo structures
            result = session.run("""
                MATCH (source:Repository {id: $repo_id})
                CALL gds.nodeSimilarity.stream('repo_structure')
                YIELD node1, node2, similarity
                WHERE id(node1) = id(source)
                RETURN gds.util.asNode(node2) as similar_repo,
                       similarity
                ORDER BY similarity DESC
                LIMIT $limit
            """, repo_id=repo_id, limit=limit)
            
            return [dict(record) for record in result]

    def find_common_patterns(self, repo_ids: List[str]) -> List[Dict[str, Any]]:
        """Find common code patterns between repositories.
        
        Uses APOC path finding to identify:
        - Shared function patterns
        - Similar module structures
        - Common dependencies
        
        Args:
            repo_ids: List of repository IDs to analyze
        """
        with self._driver.session() as session:
            result = session.run("""
                MATCH (r:Repository)
                WHERE r.id IN $repo_ids
                WITH collect(r) as repos
                CALL apoc.path.subgraphAll(repos, {
                    relationshipFilter: 'CONTAINS|CALLS|IMPORTS',
                    maxLevel: 3
                })
                YIELD nodes, relationships
                WITH nodes, relationships
                CALL apoc.stats.degrees(relationships)
                YIELD total, max, min, mean
                RETURN {
                    common_patterns: [n in nodes WHERE n:Function AND apoc.node.degree(n) > mean],
                    stats: {total: total, max: max, min: min, mean: mean}
                } as result
            """, repo_ids=repo_ids)
            
            return [dict(record) for record in result]

    def analyze_dependency_paths(self, source_repo: str, target_repo: str) -> List[Dict[str, Any]]:
        """Analyze how two repositories might be related through dependencies.
        
        Uses APOC path finding to discover:
        - Direct dependencies
        - Shared dependencies
        - Potential integration points
        
        Args:
            source_repo: Source repository ID
            target_repo: Target repository ID
        """
        with self._driver.session() as session:
            result = session.run("""
                MATCH (source:Repository {id: $source}), (target:Repository {id: $target})
                CALL apoc.path.expandConfig(source, {
                    relationshipFilter: 'IMPORTS|IMPLEMENTS|EXTENDS',
                    uniqueness: 'NODE_GLOBAL',
                    maxLevel: 4,
                    targetNodes: [target]
                })
                YIELD path
                WITH path, relationships(path) as rels
                RETURN {
                    path_length: length(path),
                    nodes: [n in nodes(path) | n.name],
                    relationship_types: [type(r) in rels],
                    common_deps: [n in nodes(path) WHERE n:Function AND 
                                apoc.node.degree.in(n, 'IMPORTS') > 1]
                } as connection
                ORDER BY length(path)
            """, source=source_repo, target=target_repo)
            
            return [dict(record) for record in result]

    def get_function_dependencies(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """Get comprehensive function dependency information.
        
        Uses APOC path finding to analyze:
        - Direct function calls
        - Transitive dependencies
        - Module relationships
        
        Args:
            file_path: Path to the file
            function_name: Name of the function
        """
        with self._driver.session() as session:
            result = session.run("""
                MATCH (f:Function {name: $name})<-[:CONTAINS]-(file:File {path: $path})
                CALL apoc.path.spanningTree(f, {
                    relationshipFilter: 'CALLS|IMPLEMENTS|USES',
                    maxLevel: 3
                })
                YIELD path
                WITH collect(path) as paths
                RETURN {
                    direct_deps: [n in apoc.coll.toSet([p in paths | nodes(p)[1]]) 
                                WHERE n:Function | n.name],
                    modules: apoc.coll.toSet([p in paths | 
                            head([(n:File) in nodes(p) | n.path])]),
                    call_chains: [p in paths | [n in nodes(p) | n.name]]
                } as dependencies
            """, path=file_path, name=function_name)
            
            return result.single() or {}

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect() 