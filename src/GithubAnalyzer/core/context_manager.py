from typing import Dict, Any, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from .models import (
    QueryContext, 
    ContextAnalysisResult,
    CodeContextAnalyzer
)
import logging
import ast
from .registry import BusinessTools
from .patterns import PatternDetector
from .embeddings import CodeEmbeddingGenerator
from .utils import setup_logger

logger = setup_logger(__name__)

class ContextManager:
    """Manages code context analysis and relationships"""
    
    def __init__(self):
        self.tools = BusinessTools.create()
        self.embedding_generator = CodeEmbeddingGenerator()
        self.context_analyzer = CodeContextAnalyzer()
        
    def build_context(self, code: str, file_path: str = None) -> ContextAnalysisResult:
        """Build comprehensive context for code understanding"""
        try:
            # Get cached context if available
            if file_path:
                cached = self.tools.db_manager.get_from_cache(file_path, "context")
                if cached:
                    return cached

            # Get base context from analyzer
            context = self.context_analyzer.analyze_context(code)
            
            # Add file-specific context
            if file_path:
                context = self._add_file_context(context, file_path)
                
            # Add usage patterns using PatternDetector
            parse_result = self.code_parser.parse_content(code)
            patterns = PatternDetector.detect_all(parse_result, file_path)
            context.project_patterns.extend(patterns['usage'])
            
            # Generate enhanced embeddings
            context.embeddings = self.embedding_generator.generate_contextual_embedding(
                code, 
                {
                    'imports': context.imports,
                    'file_path': file_path,
                    'project_style': context.style_patterns,
                    'common_patterns': context.project_patterns
                }
            )
                
            # Cache results
            if file_path:
                self.tools.db_manager.store_in_cache(file_path, "context", context)
                
            return context
            
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return ContextAnalysisResult()

    def _add_file_context(self, context: ContextAnalysisResult, file_path: str) -> ContextAnalysisResult:
        """Add file-specific context information"""
        try:
            # Get repository-level context
            repo_context = self.tools.db_manager.get_repository_info(file_path)
            if repo_context:
                context.project_patterns.extend(repo_context.metadata.get('patterns', []))
                
            # Use PatternDetector for all pattern detection
            parse_result = self.code_parser.parse_file(file_path)
            patterns = PatternDetector.detect_all(parse_result, file_path)
            
            context.framework_patterns.extend(patterns['framework'])
            context.style_patterns.extend(patterns['style'])
            context.project_patterns.extend(patterns['architectural'])
            
            return context
            
        except Exception as e:
            logger.error(f"Error adding file context: {e}")
            return context

    def _detect_style_patterns(self, file_path: str) -> List[str]:
        """Detect coding style patterns"""
        patterns = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check naming conventions
            if '_' in content:
                patterns.append('snake_case')
            if any(c.isupper() for c in content):
                patterns.append('PascalCase')
                
            # Check docstring style
            if '"""' in content:
                patterns.append('docstring_double')
            elif "'''" in content:
                patterns.append('docstring_single')
                
            # Check import style
            if 'from typing import' in content:
                patterns.append('type_hints')
                
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting style patterns: {e}")
            return patterns

    def update_context(self, context: ContextAnalysisResult, new_code: str) -> ContextAnalysisResult:
        """Update existing context with new code"""
        try:
            new_context = self.context_analyzer.analyze_context(new_code)
            
            # Merge contexts
            context.imports.extend(new_context.imports)
            context.related_functions.extend(new_context.related_functions)
            context.class_hierarchy.extend(new_context.class_hierarchy)
            
            # Update embeddings
            if new_context.embeddings is not None:
                if context.embeddings is None:
                    context.embeddings = new_context.embeddings
                else:
                    context.embeddings = np.mean([context.embeddings, new_context.embeddings], axis=0)
                    
            return context
            
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            return context 

    def _extract_project_patterns(self, context: Dict[str, Any]) -> str:
        """Extract project-specific patterns"""
        return ' '.join([
            context.get('project_style', ''),
            context.get('common_patterns', ''),
            context.get('team_conventions', '')
        ])

    def generate_contextual_embedding(self, code: str, context: Dict[str, Any]) -> np.ndarray:
        """Generate embeddings with full context consideration"""
        context_features = [
            self._extract_project_patterns(context),
            ' '.join(self._detect_style_patterns(context.get('file_path', ''))),
            ' '.join(self._extract_usage_patterns(code))
        ]
        
        combined_input = code + ' ' + ' '.join(filter(None, context_features))
        return self.embedding_model.encode(combined_input) 