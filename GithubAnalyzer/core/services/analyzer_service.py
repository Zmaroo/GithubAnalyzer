from typing import Dict, Any, List, Optional
from pathlib import Path
import os
from .base_service import BaseService
from ..models import (
    FunctionInfo,
    ClassInfo,
    ModuleInfo,
    AnalysisResult,
    AnalysisContext,
    CodeRelationships,
    ParseResult
)
from ..utils.logging import setup_logger
from ...config.settings import settings
from ..utils.file_utils import FileDiscovery

logger = setup_logger(__name__)

class AnalyzerService(BaseService):
    """Service for code analysis operations"""
    
    def _initialize(self) -> None:
        self.current_file = None
        self.file_discovery = FileDiscovery()
        
    def analyze_repository(self, repo_path: str) -> AnalysisResult:
        """Analyze entire repository"""
        try:
            modules = []
            relationships = CodeRelationships()
            
            for file_batch in self.file_discovery.discover_files_batched(
                repo_path, 
                settings.BATCH_SIZE
            ):
                for file_path in file_batch:
                    module_info = self.analyze_file(file_path)
                    if module_info:
                        modules.append(module_info)
                        
            return AnalysisResult(
                modules=modules,
                relationships=relationships
            )
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            return None

    def analyze_file(self, file_path: str) -> Optional[ModuleInfo]:
        """Analyze a single file"""
        try:
            self.current_file = file_path
            
            # Skip non-code files and excluded patterns
            if not self._should_analyze_file(file_path):
                return None
                
            # Parse file using appropriate parser
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            parse_result = self.tools.parser_service.parse_file(file_path, content)
            if not parse_result.success:
                logger.warning(f"Failed to parse {file_path}: {parse_result.errors}")
                return None
                
            return self._create_module_info(file_path, parse_result)
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return None
        finally:
            self.current_file = None

    def _should_analyze_file(self, file_path: str) -> bool:
        """Check if file should be analyzed"""
        path = Path(file_path)
        return (
            path.suffix in settings.SUPPORTED_EXTENSIONS and
            not any(pattern in path.parts for pattern in settings.EXCLUDE_PATTERNS)
        )

    def _create_module_info(self, file_path: str, parse_result: ParseResult) -> ModuleInfo:
        """Create ModuleInfo from parse results"""
        semantic = parse_result.semantic
        
        return ModuleInfo(
            path=file_path,
            imports=semantic.get('imports', []),
            functions=[
                FunctionInfo(
                    name=func['name'],
                    docstring=func.get('docstring'),
                    args=func.get('params', []),
                    returns=func.get('returns'),
                    start_line=func.get('start_line', 0),
                    end_line=func.get('end_line', 0)
                )
                for func in semantic.get('functions', [])
            ],
            classes=[
                ClassInfo(
                    name=cls['name'],
                    docstring=cls.get('docstring'),
                    methods=[
                        FunctionInfo(
                            name=method['name'],
                            docstring=method.get('docstring'),
                            args=method.get('params', []),
                            returns=method.get('returns'),
                            start_line=method.get('start_line', 0),
                            end_line=method.get('end_line', 0)
                        )
                        for method in cls.get('methods', [])
                    ],
                    bases=cls.get('bases', [])
                )
                for cls in semantic.get('classes', [])
            ]
        ) 