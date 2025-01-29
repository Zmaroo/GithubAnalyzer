"""Neo4j service for storing code relationships with advanced graph analytics."""
from typing import Dict, List, Any, Optional, Set
from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv

from GithubAnalyzer.models.core.database import File, Function
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

class Neo4jService:
    """Service for Neo4j graph database operations."""
    
    def __init__(self):
        """Initialize Neo4j service with GDS and APOC support."""
        load_dotenv()
        self._driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USERNAME", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "adminadmin")
            )
        )
        self._setup_gds_procedures()
        
    def _setup_gds_procedures(self) -> None:
        """Setup Graph Data Science procedures and verify plugin availability."""
        with self._driver.session() as session:
            # Verify GDS plugin
            session.run("CALL gds.list()")
            # Verify APOC plugin
            session.run("CALL apoc.help('apoc')")
            
    def analyze_code_dependencies(self, repo_id: str) -> Dict[str, Any]:
        """Analyze code dependencies using GDS algorithms.
        
        Uses PageRank and betweenness centrality to identify:
        - Most important functions/classes (high PageRank)
        - Critical path components (high betweenness)
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            Dictionary containing analysis results
        """
        with self._driver.session() as session:
            # Create graph projection for analysis
            session.run("""
                CALL gds.graph.project(
                    'code_deps',
                    ['Function', 'Class'],
                    {
                        CALLS: {
                            type: 'CALLS',
                            orientation: 'NATURAL'
                        },
                        CONTAINS: {
                            type: 'CONTAINS',
                            orientation: 'NATURAL'
                        }
                    }
                )
            """)
            
            # Run PageRank
            pagerank_result = session.run("""
                CALL gds.pageRank.stream('code_deps')
                YIELD nodeId, score
                WITH gds.util.asNode(nodeId) as node, score
                WHERE node.repo_id = $repo_id
                RETURN node.name as name, node.type as type, score
                ORDER BY score DESC
                LIMIT 10
            """, repo_id=repo_id)
            
            # Run betweenness centrality
            betweenness_result = session.run("""
                CALL gds.betweenness.stream('code_deps')
                YIELD nodeId, score
                WITH gds.util.asNode(nodeId) as node, score
                WHERE node.repo_id = $repo_id
                RETURN node.name as name, node.type as type, score
                ORDER BY score DESC
                LIMIT 10
            """, repo_id=repo_id)
            
            # Cleanup projection
            session.run("CALL gds.graph.drop('code_deps')")
            
            return {
                'central_components': [dict(record) for record in pagerank_result],
                'critical_paths': [dict(record) for record in betweenness_result]
            }
            
    def find_similar_code_patterns(self, file_path: str) -> List[Dict[str, Any]]:
        """Find similar code patterns using node similarity algorithms.
        
        Uses GDS node similarity to identify similar:
        - Function implementations
        - Class structures
        - Code patterns
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of similar code patterns
        """
        with self._driver.session() as session:
            # Create graph projection for similarity analysis
            session.run("""
                CALL gds.graph.project(
                    'code_similarity',
                    ['Function', 'Class'],
                    {
                        CALLS: {
                            type: 'CALLS',
                            orientation: 'NATURAL',
                            properties: ['weight']
                        }
                    },
                    {
                        nodeProperties: ['ast_data']
                    }
                )
            """)
            
            # Run node similarity
            result = session.run("""
                CALL gds.nodeSimilarity.stream('code_similarity')
                YIELD node1, node2, similarity
                WITH 
                    gds.util.asNode(node1) as first,
                    gds.util.asNode(node2) as second,
                    similarity
                WHERE first.file_path = $file_path
                RETURN 
                    first.name as source_name,
                    second.name as similar_name,
                    second.file_path as similar_file,
                    similarity
                ORDER BY similarity DESC
                LIMIT 5
            """, file_path=file_path)
            
            # Cleanup projection
            session.run("CALL gds.graph.drop('code_similarity')")
            
            return [dict(record) for record in result]
            
    def detect_code_communities(self, repo_id: str) -> Dict[str, List[str]]:
        """Detect code communities using GDS community detection.
        
        Uses Louvain algorithm to identify:
        - Related code components
        - Modular structures
        - Potential microservices
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            Dictionary mapping community IDs to component lists
        """
        with self._driver.session() as session:
            # Create graph projection
            session.run("""
                CALL gds.graph.project(
                    'code_communities',
                    ['Function', 'Class'],
                    ['CALLS', 'CONTAINS']
                )
            """)
            
            # Run Louvain community detection
            result = session.run("""
                CALL gds.louvain.stream('code_communities')
                YIELD nodeId, communityId
                WITH 
                    gds.util.asNode(nodeId) as node,
                    communityId
                WHERE node.repo_id = $repo_id
                WITH communityId, collect(node.name) as components
                RETURN communityId, components
                ORDER BY size(components) DESC
            """, repo_id=repo_id)
            
            # Cleanup projection
            session.run("CALL gds.graph.drop('code_communities')")
            
            return {
                f"community_{record['communityId']}": record['components']
                for record in result
            }
            
    def find_code_paths(self, start_func: str, end_func: str, repo_id: str) -> List[List[str]]:
        """Find paths between code components using GDS path finding.
        
        Uses shortest path algorithms to identify:
        - Dependency chains
        - Call hierarchies
        - Component relationships
        
        Args:
            start_func: Starting function name
            end_func: Ending function name
            repo_id: Repository identifier
            
        Returns:
            List of paths (each path is a list of function names)
        """
        with self._driver.session() as session:
            # Create graph projection
            session.run("""
                CALL gds.graph.project(
                    'code_paths',
                    'Function',
                    'CALLS'
                )
            """)
            
            # Find all paths
            result = session.run("""
                MATCH (start:Function {name: $start, repo_id: $repo_id})
                MATCH (end:Function {name: $end, repo_id: $repo_id})
                CALL gds.allShortestPaths.stream('code_paths', {
                    sourceNode: id(start),
                    targetNode: id(end)
                })
                YIELD path
                RETURN [node in nodes(path) | node.name] as path_names
            """, start=start_func, end=end_func, repo_id=repo_id)
            
            # Cleanup projection
            session.run("CALL gds.graph.drop('code_paths')")
            
            return [record['path_names'] for record in result]
            
    def export_graph_data(self, repo_id: str, format: str = 'json') -> str:
        """Export graph data using APOC export procedures.
        
        Args:
            repo_id: Repository identifier
            format: Export format ('json' or 'cypher')
            
        Returns:
            Exported data as string
        """
        with self._driver.session() as session:
            if format == 'json':
                result = session.run("""
                    MATCH (n)
                    WHERE n.repo_id = $repo_id
                    CALL apoc.export.json.query(
                        "MATCH (n)-[r]->(m) WHERE n.repo_id = $repo_id RETURN n, r, m",
                        null,
                        {params: {repo_id: $repo_id}}
                    )
                    YIELD data
                    RETURN data
                """, repo_id=repo_id)
            else:
                result = session.run("""
                    CALL apoc.export.cypher.query(
                        "MATCH (n)-[r]->(m) WHERE n.repo_id = $repo_id RETURN n, r, m",
                        null,
                        {params: {repo_id: $repo_id}}
                    )
                    YIELD cypherStatements
                    RETURN cypherStatements
                """, repo_id=repo_id)
                
            return result.single()[0]
            
    def import_graph_data(self, data: str, format: str = 'json') -> None:
        """Import graph data using APOC import procedures.
        
        Args:
            data: Data to import
            format: Import format ('json' or 'cypher')
        """
        with self._driver.session() as session:
            if format == 'json':
                session.run("""
                    CALL apoc.import.json($data)
                """, data=data)
            else:
                session.run("""
                    CALL apoc.cypher.runMany($data)
                """, data=data)
        
    def setup_constraints(self) -> None:
        """Set up Neo4j constraints and indexes."""
        with self._driver.session() as session:
            # File node constraints
            session.run("""
                CREATE CONSTRAINT file_unique IF NOT EXISTS
                FOR (f:File) REQUIRE (f.repo_id, f.path) IS UNIQUE
            """)
            
            # Function node constraints
            session.run("""
                CREATE CONSTRAINT function_unique IF NOT EXISTS
                FOR (f:Function) REQUIRE (f.repo_id, f.file_path, f.name) IS UNIQUE
            """)
            
            # Class node constraints
            session.run("""
                CREATE CONSTRAINT class_unique IF NOT EXISTS
                FOR (c:Class) REQUIRE (c.repo_id, c.file_path, c.name) IS UNIQUE
            """)
            
            # Language constraints
            session.run("""
                CREATE CONSTRAINT language_unique IF NOT EXISTS
                FOR (l:Language) REQUIRE l.name IS UNIQUE
            """)
            
            # Create indexes for common queries
            session.run("""
                CREATE INDEX file_language_idx IF NOT EXISTS
                FOR (f:File) ON (f.language)
            """)
            
            session.run("""
                CREATE INDEX function_language_idx IF NOT EXISTS
                FOR (f:Function) ON (f.language)
            """)
            
            session.run("""
                CREATE INDEX class_language_idx IF NOT EXISTS
                FOR (c:Class) ON (c.language)
            """)
            
    def create_file_node(self, file: File) -> None:
        """Create a file node with language information."""
        with self._driver.session() as session:
            # Create Language node if it doesn't exist
            session.run("""
                MERGE (l:Language {name: $language})
                WITH l
                MERGE (f:File {repo_id: $repo_id, path: $path})
                SET f.language = $language,
                    f.created_at = datetime()
                MERGE (f)-[:HAS_LANGUAGE]->(l)
            """, {
                'repo_id': file.repo_id,
                'path': file.path,
                'language': file.language
            })
            
    def create_function_node(self, function: Function, ast_data: Dict[str, Any]) -> None:
        """Create a function node with AST information."""
        with self._driver.session() as session:
            session.run("""
                MATCH (f:File {repo_id: $repo_id, path: $file_path})
                MERGE (fn:Function {
                    repo_id: $repo_id,
                    file_path: $file_path,
                    name: $name
                })
                SET fn.language = f.language,
                    fn.ast_data = $ast_data,
                    fn.start_point = $start_point,
                    fn.end_point = $end_point,
                    fn.created_at = datetime()
                MERGE (f)-[:CONTAINS]->(fn)
            """, {
                'repo_id': function.repo_id,
                'file_path': function.file_path,
                'name': function.name,
                'ast_data': json.dumps(ast_data),
                'start_point': json.dumps(ast_data.get('start_point')),
                'end_point': json.dumps(ast_data.get('end_point'))
            })
            
    def create_class_node(self, repo_id: str, file_path: str, class_name: str,
                         ast_data: Dict[str, Any]) -> None:
        """Create a class node with AST information."""
        with self._driver.session() as session:
            session.run("""
                MATCH (f:File {repo_id: $repo_id, path: $file_path})
                MERGE (c:Class {
                    repo_id: $repo_id,
                    file_path: $file_path,
                    name: $name
                })
                SET c.language = f.language,
                    c.ast_data = $ast_data,
                    c.start_point = $start_point,
                    c.end_point = $end_point,
                    c.created_at = datetime()
                MERGE (f)-[:CONTAINS]->(c)
            """, {
                'repo_id': repo_id,
                'file_path': file_path,
                'name': class_name,
                'ast_data': json.dumps(ast_data),
                'start_point': json.dumps(ast_data.get('start_point')),
                'end_point': json.dumps(ast_data.get('end_point'))
            })
            
    def create_function_relationship(self, caller: Function, callee: Function) -> None:
        """Create a relationship between functions."""
        with self._driver.session() as session:
            session.run("""
                MATCH (caller:Function {
                    repo_id: $caller_repo_id,
                    file_path: $caller_file_path,
                    name: $caller_name
                })
                MATCH (callee:Function {
                    repo_id: $callee_repo_id,
                    file_path: $callee_file_path,
                    name: $callee_name
                })
                MERGE (caller)-[r:CALLS]->(callee)
                SET r.created_at = datetime()
            """, {
                'caller_repo_id': caller.repo_id,
                'caller_file_path': caller.file_path,
                'caller_name': caller.name,
                'callee_repo_id': callee.repo_id,
                'callee_file_path': callee.file_path,
                'callee_name': callee.name
            })
            
    def get_file_relationships(self, file_path: str) -> Dict[str, Any]:
        """Get all relationships for a file."""
        with self._driver.session() as session:
            result = session.run("""
                MATCH (f:File {path: $file_path})
                OPTIONAL MATCH (f)-[:CONTAINS]->(fn:Function)
                OPTIONAL MATCH (f)-[:CONTAINS]->(c:Class)
                OPTIONAL MATCH (fn)-[r:CALLS]->(called:Function)
                RETURN f.language as language,
                       collect(DISTINCT {
                           type: 'function',
                           name: fn.name,
                           ast_data: fn.ast_data,
                           calls: collect(DISTINCT {
                               name: called.name,
                               file_path: called.file_path
                           })
                       }) as functions,
                       collect(DISTINCT {
                           type: 'class',
                           name: c.name,
                           ast_data: c.ast_data
                       }) as classes
            """, file_path=file_path)
            
            data = result.single()
            if not data:
                return {}
                
            return {
                'language': data['language'],
                'functions': [
                    {
                        'name': f['name'],
                        'ast_data': json.loads(f['ast_data']) if f['ast_data'] else None,
                        'calls': f['calls']
                    }
                    for f in data['functions'] if f['name']
                ],
                'classes': [
                    {
                        'name': c['name'],
                        'ast_data': json.loads(c['ast_data']) if c['ast_data'] else None
                    }
                    for c in data['classes'] if c['name']
                ]
            }
            
    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships from the graph database."""
        with self._driver.session() as session:
            result = session.run("""
                MATCH (f:File)
                OPTIONAL MATCH (f)-[:CONTAINS]->(fn:Function)
                OPTIONAL MATCH (fn)-[r:CALLS]->(called:Function)
                WITH f, fn, collect({
                    name: called.name,
                    file_path: called.file_path,
                    type: 'CALLS'
                }) as calls
                RETURN f.path as file_path,
                       collect({
                           name: fn.name,
                           relationships: calls
                       }) as relationships
            """)
            
            return [
                {
                    'file_path': record['file_path'],
                    'relationships': {
                        rel['name']: rel['relationships']
                        for rel in record['relationships']
                        if rel['name']  # Filter out None names
                    }
                }
                for record in result
            ]
            
    def delete_file_nodes(self, repo_id: str, file_path: str) -> None:
        """Delete all nodes related to a file.
        
        This includes:
        - The file node itself
        - All function nodes contained in the file
        - All class nodes contained in the file
        - All relationships involving these nodes
        
        Args:
            repo_id: Repository identifier
            file_path: Path to the file
        """
        with self._driver.session() as session:
            # Delete all nodes and their relationships
            session.run("""
                MATCH (f:File {repo_id: $repo_id, path: $path})
                OPTIONAL MATCH (f)-[:CONTAINS]->(n)
                DETACH DELETE f, n
            """, {
                'repo_id': repo_id,
                'path': file_path
            })
            
    def get_language_nodes(self) -> List[Dict[str, Any]]:
        """Get all language nodes and their relationships."""
        with self._driver.session() as session:
            result = session.run("""
                MATCH (l:Language)
                OPTIONAL MATCH (f:File)-[:HAS_LANGUAGE]->(l)
                WITH l, collect({
                    path: f.path,
                    repo_id: f.repo_id
                }) as files
                RETURN l.name as language,
                       files
            """)
            
            return [
                {
                    'language': record['language'],
                    'files': [
                        f for f in record['files']
                        if f['path']  # Filter out None paths
                    ]
                }
                for record in result
            ]
            
    def sync_language_nodes(self, languages: Set[str]) -> None:
        """Synchronize language nodes with a set of languages.
        
        Args:
            languages: Set of language identifiers to sync
        """
        with self._driver.session() as session:
            # Create missing language nodes
            for lang in languages:
                session.run("""
                    MERGE (l:Language {name: $name})
                """, {'name': lang})
                
            # Delete obsolete language nodes
            session.run("""
                MATCH (l:Language)
                WHERE NOT l.name IN $languages
                DETACH DELETE l
            """, {'languages': list(languages)})
            
    def update_file_language(self, file_path: str, language: str) -> None:
        """Update the language of a file node.
        
        Args:
            file_path: Path to the file
            language: New language identifier
        """
        with self._driver.session() as session:
            session.run("""
                MATCH (f:File {path: $path})
                OPTIONAL MATCH (f)-[r:HAS_LANGUAGE]->(:Language)
                DELETE r
                WITH f
                MERGE (l:Language {name: $language})
                MERGE (f)-[:HAS_LANGUAGE]->(l)
                SET f.language = $language
            """, {
                'path': file_path,
                'language': language
            })
            
    def close(self) -> None:
        """Close the Neo4j connection."""
        self._driver.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def get_graph_statistics(self, repo_id: Optional[int] = None) -> Dict[str, int]:
        """Get statistics about the graph structure.
        
        Args:
            repo_id: Optional repository ID to filter by
            
        Returns:
            Dictionary containing counts of different node and relationship types
        """
        stats = {}
        
        # Node count queries
        if repo_id:
            stats.update({
                'file_count': self._execute_query(
                    "MATCH (f:File) WHERE f.repo_id = $repo_id RETURN COUNT(f) as count",
                    {'repo_id': repo_id}
                )[0]['count'],
                'function_count': self._execute_query(
                    "MATCH (fn:Function) WHERE fn.repo_id = $repo_id RETURN COUNT(fn) as count",
                    {'repo_id': repo_id}
                )[0]['count'],
                'class_count': self._execute_query(
                    "MATCH (c:Class) WHERE c.repo_id = $repo_id RETURN COUNT(c) as count",
                    {'repo_id': repo_id}
                )[0]['count']
            })
        else:
            stats.update({
                'file_count': self._execute_query("MATCH (f:File) RETURN COUNT(f) as count")[0]['count'],
                'function_count': self._execute_query("MATCH (fn:Function) RETURN COUNT(fn) as count")[0]['count'],
                'class_count': self._execute_query("MATCH (c:Class) RETURN COUNT(c) as count")[0]['count']
            })
            
        # Relationship count queries
        if repo_id:
            stats.update({
                'calls_count': self._execute_query(
                    """MATCH (fn:Function)-[r:CALLS]->() 
                       WHERE fn.repo_id = $repo_id 
                       RETURN COUNT(r) as count""",
                    {'repo_id': repo_id}
                )[0]['count'],
                'contains_count': self._execute_query(
                    """MATCH (f:File)-[r:CONTAINS]->() 
                       WHERE f.repo_id = $repo_id 
                       RETURN COUNT(r) as count""",
                    {'repo_id': repo_id}
                )[0]['count'],
                'imports_count': self._execute_query(
                    """MATCH (f:File)-[r:IMPORTS]->() 
                       WHERE f.repo_id = $repo_id 
                       RETURN COUNT(r) as count""",
                    {'repo_id': repo_id}
                )[0]['count']
            })
        else:
            stats.update({
                'calls_count': self._execute_query("MATCH ()-[r:CALLS]->() RETURN COUNT(r) as count")[0]['count'],
                'contains_count': self._execute_query("MATCH ()-[r:CONTAINS]->() RETURN COUNT(r) as count")[0]['count'],
                'imports_count': self._execute_query("MATCH ()-[r:IMPORTS]->() RETURN COUNT(r) as count")[0]['count']
            })
            
        return stats

    def _execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a Neo4j query.
        
        Args:
            query: Cypher query to execute
            params: Optional query parameters
            
        Returns:
            List of result records as dictionaries
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self._driver.session() as session:
                result = session.run(query, params or {})
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise 