from typing import Dict, Any, Callable, Type, List
from dataclasses import dataclass, field
from .database_utils import DatabaseManager
from .code_analyzer import CodeAnalyzer
from .repository_manager import RepositoryManager
from .query_processor import QueryProcessor
from .documentation_analyzer import DocumentationAnalyzer
from .utils import setup_logger
from .tree_sitter_service import TreeSitterService

logger = setup_logger(__name__)

@dataclass
class BusinessTools:
    """Single source of truth for all business tools"""
    db_manager: DatabaseManager
    code_analyzer: CodeAnalyzer
    repo_manager: RepositoryManager
    query_processor: QueryProcessor
    doc_analyzer: DocumentationAnalyzer
    tree_sitter_service: TreeSitterService

    @classmethod
    def create(cls) -> 'BusinessTools':
        """Factory method to create properly initialized tools"""
        db_manager = DatabaseManager()
        tree_sitter_service = TreeSitterService()
        return cls(
            db_manager=db_manager,
            code_analyzer=CodeAnalyzer(db_manager),
            repo_manager=RepositoryManager(db_manager),
            query_processor=QueryProcessor(db_manager),
            doc_analyzer=DocumentationAnalyzer(),
            tree_sitter_service=tree_sitter_service
        )

    def get_tools(self) -> Dict[str, Callable]:
        """Get all available tools"""
        return {
            # Repository tools
            "clone_repository": self.repo_manager.clone_repository,
            "discover_files": self.repo_manager.discover_files,
            "cleanup_repo": self.repo_manager.cleanup_repo,
            "analyze_repo": self.repo_manager.analyze_repo,
            
            # Analysis tools
            "analyze_repository": self.code_analyzer.analyze_repository,
            "analyze_dependencies": self.code_analyzer.analyze_dependencies,
            "analyze_patterns": self.code_analyzer.analyze_patterns,
            
            # Documentation tools
            "analyze_documentation": self.doc_analyzer.analyze_file,
            "extract_docstrings": self.doc_analyzer.extract_docstrings,
            
            # Query tools
            "query_repository": self.query_processor.query_repository,
            
            # Database tools
            "store_analysis": self.db_manager.store_repository_info,
            "get_analysis": self.db_manager.get_repository_info,
            "clear_cache": self.db_manager.clear_cache
        } 

    def detect_patterns(self, parse_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """Single entry point for all pattern detection"""
        return {
            'structural': self._detect_structural_patterns(parse_result),
            'design': self._detect_design_patterns(parse_result),
            'usage': self._detect_usage_patterns(parse_result),
            'architectural': self._detect_architectural_patterns(parse_result)
        }

    # Move all pattern detection methods here as private methods
    def _detect_structural_patterns(self, parse_result: Dict[str, Any]) -> List[str]:
        """Detect structural code patterns"""
        # Implementation from PatternDetector
        pass

    # ... other pattern detection methods 