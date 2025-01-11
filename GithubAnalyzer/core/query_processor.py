from typing import Dict, Any, Optional
import logging
from .registry import BusinessTools
from .models import QueryResponse

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, db_manager=None):
        self.tools = BusinessTools.create()
        # Keep db_manager param for backward compatibility

    def query_repository(self, question: str) -> QueryResponse:
        """Query the analyzed repository with natural language questions"""
        try:
            # Get repository info and analysis results
            repo_info = self.db_manager.get_repository_info()
            if not repo_info:
                return QueryResponse(
                    response="Repository information not found in database.",
                    confidence=0.0
                )

            # Get cached analysis
            analysis = self.db_manager.get_from_cache(repo_info['name'], 'analysis')
            if not analysis:
                return QueryResponse(
                    response="Analysis data not found. Try re-analyzing the repository.",
                    confidence=0.0
                )

            # Construct context from available data
            context = {
                'repository': repo_info,
                'code_structure': analysis.get('analysis', {}).get('code', {}),
                'documentation': analysis.get('analysis', {}).get('documentation', {}),
                'relationships': self._get_code_relationships(repo_info['name'])
            }

            # Generate response
            response = self._generate_response(question, context)
            
            return QueryResponse(
                response=response,
                confidence=0.8 if response != "Sorry, I encountered an error while trying to answer your question." else 0.0,
                context_used=context
            )

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return QueryResponse(
                response=f"Error processing query: {e}",
                confidence=0.0
            )

    def _get_code_relationships(self, repo_name: str) -> Dict[str, Any]:
        """Get code relationships from Neo4j"""
        relationships = {
            'modules': [],
            'dependencies': [],
            'classes': [],
            'functions': []
        }
        
        if not self.db_manager.neo4j_driver:
            return relationships

        try:
            with self.db_manager.get_neo4j_session() as session:
                # Get modules
                result = session.run("""
                    MATCH (r:Repository {name: $repo_name})<-[:BELONGS_TO]-(m:Module)
                    RETURN m.path as path
                """, repo_name=repo_name)
                relationships['modules'] = [record['path'] for record in result]

                # Get dependencies
                result = session.run("""
                    MATCH (r:Repository {name: $repo_name})<-[:BELONGS_TO]-(m:Module)-[:IMPORTS]->(i:Import)
                    RETURN i.name as name
                """, repo_name=repo_name)
                relationships['dependencies'] = [record['name'] for record in result]

                # Get classes with inheritance
                result = session.run("""
                    MATCH (r:Repository {name: $repo_name})<-[:BELONGS_TO]-(m:Module)<-[:DEFINED_IN]-(c:Class)
                    OPTIONAL MATCH (c)-[:INHERITS_FROM]->(base:Class)
                    RETURN c.name as name, collect(base.name) as bases
                """, repo_name=repo_name)
                relationships['classes'] = [
                    {'name': record['name'], 'bases': record['bases']}
                    for record in result
                ]

                # Get functions
                result = session.run("""
                    MATCH (r:Repository {name: $repo_name})<-[:BELONGS_TO]-(m:Module)<-[:DEFINED_IN]-(f:Function)
                    RETURN f.name as name, f.lineno as lineno
                """, repo_name=repo_name)
                relationships['functions'] = [
                    {'name': record['name'], 'lineno': record['lineno']}
                    for record in result
                ]

        except Exception as e:
            logger.error(f"Error getting code relationships: {e}")

        return relationships

    def _generate_response(self, question: str, context: Dict[str, Any]) -> str:
        """Generate a response to the question based on repository context"""
        try:
            # Basic response generation based on available data
            if "what" in question.lower():
                if "repository" in question.lower():
                    repo_name = context['repository'].get('name', 'Unknown')
                    doc = context['documentation'].get('readme', {}).get('content', '')
                    if doc:
                        return f"{repo_name} is a repository that {doc[:200]}..."
                    return f"This is the {repo_name} repository."
                
            elif "how many" in question.lower():
                code = context['code_structure']
                if "files" in question.lower() or "modules" in question.lower():
                    count = len(context['relationships']['modules'])
                    return f"The repository contains {count} Python modules."
                elif "class" in question.lower():
                    count = len(context['relationships']['classes'])
                    return f"The repository contains {count} classes."
                elif "function" in question.lower():
                    count = len(context['relationships']['functions'])
                    return f"The repository contains {count} functions."
                
            elif "dependencies" in question.lower():
                deps = context['relationships']['dependencies']
                return f"The repository depends on: {', '.join(deps)}"

            # Default response
            return "I understand your question but don't have enough context to provide a specific answer. Try asking about the repository structure, classes, functions, or dependencies."

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error while trying to answer your question." 