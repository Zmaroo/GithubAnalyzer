"""Code analyzer service."""

import logging
from typing import Any, Dict, List, Optional

from GithubAnalyzer.models.analysis.analysis import AnalysisResult, CodeAnalysis
from GithubAnalyzer.models.core.errors import ServiceError
from GithubAnalyzer.services.core.base_service import BaseService
from GithubAnalyzer.services.core.parser_service import ParserService


class AnalyzerService(BaseService):
    """Service for analyzing code."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the analyzer.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._parser: Optional[ParserService] = None
        self._initialized = False

    def initialize(self, parser: ParserService) -> None:
        """Initialize the analyzer service.

        Args:
            parser: Parser service instance

        Raises:
            ServiceError: If initialization fails
        """
        try:
            self._parser = parser
            self._initialized = True
            self.logger.info("Analyzer service initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize analyzer: %s", str(e))
            raise ServiceError(f"Failed to initialize analyzer: {str(e)}")

    def analyze_code(self, content: str) -> CodeAnalysis:
        """Analyze code content.

        Args:
            content: Code content to analyze

        Returns:
            Code analysis result

        Raises:
            ServiceError: If analysis fails
        """
        if not self._initialized:
            raise ServiceError("Analyzer service not initialized")

        try:
            # Parse code
            parse_result = self._parser.parse(content)

            # Analyze AST
            metrics = self._calculate_metrics(parse_result["ast"])
            dependencies = self._extract_dependencies(parse_result["ast"])
            patterns = self._detect_patterns(parse_result["ast"])

            return CodeAnalysis(
                content=content,
                ast=parse_result["ast"],
                metrics=metrics,
                dependencies=dependencies,
                patterns=patterns,
                errors=[],
                metadata=parse_result.get("metadata", {}),
            )
        except Exception as e:
            self.logger.error("Failed to analyze code: %s", str(e))
            raise ServiceError(f"Failed to analyze code: {str(e)}")

    def analyze_files(self, file_paths: List[str]) -> AnalysisResult:
        """Analyze multiple code files.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Analysis result for all files
        """
        if not self._initialized:
            raise ServiceError("Analyzer service not initialized")

        analyses = []
        errors = []

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                analyses.append(self.analyze_code(content))
            except Exception as e:
                errors.append(f"Failed to analyze {file_path}: {str(e)}")

        return AnalysisResult(
            files_analyzed=len(file_paths),
            successful_analyses=len(analyses),
            failed_analyses=len(errors),
            analyses=analyses,
            errors=errors,
        )

    def _calculate_metrics(self, ast: Any) -> Dict[str, Any]:
        """Calculate code metrics from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            Dictionary of metric names and values
        """
        return {"complexity": 0, "maintainability": 0, "lines_of_code": 0}

    def _extract_dependencies(self, ast: Any) -> List[Dict[str, str]]:
        """Extract code dependencies from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            List of dependency information
        """
        return []

    def _detect_patterns(self, ast: Any) -> List[str]:
        """Detect code patterns from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            List of detected pattern names
        """
        return []

    def cleanup(self) -> None:
        """Clean up analyzer resources."""
        self._parser = None
        self._initialized = False
