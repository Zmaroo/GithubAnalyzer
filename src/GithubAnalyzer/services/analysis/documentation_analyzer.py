"""Documentation analyzer service."""

import ast
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from GithubAnalyzer.models.analysis.analysis import AnalysisError
from GithubAnalyzer.models.core.base import BaseModel
from GithubAnalyzer.services.core.base_service import BaseService


@dataclass
class DocstringInfo(BaseModel):
    """Information about a docstring."""

    content: str
    style: str
    line_count: int
    has_args: bool
    has_returns: bool
    has_raises: bool


@dataclass
class CommentInfo(BaseModel):
    """Information about a comment."""

    content: str
    line_number: int
    is_inline: bool


@dataclass
class DocumentationAnalysis(BaseModel):
    """Result of documentation analysis."""

    docstrings: List[DocstringInfo]
    comments: List[CommentInfo]
    total_lines: int
    doc_coverage: float
    style_consistency: float
    quality_score: float


@dataclass
class DocumentationMetrics(BaseModel):
    """Metrics for documentation analysis."""

    total_files: int = 0
    documented_files: int = 0
    total_functions: int = 0
    documented_functions: int = 0
    total_classes: int = 0
    documented_classes: int = 0
    coverage_score: float = 0.0


class DocumentationAnalyzer(BaseService):
    """Service for analyzing code documentation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the analyzer.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.metrics = DocumentationMetrics()

    def analyze_docstrings(self, content: str) -> List[DocstringInfo]:
        """Analyze docstrings in code content.

        Args:
            content: Code content to analyze

        Returns:
            List of DocstringInfo objects
        """
        docstrings = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        docstrings.append(self._analyze_docstring(docstring))
        except Exception as e:
            self.logger.error("Error analyzing docstrings: %s", str(e))
        return docstrings

    def analyze_comments(self, content: str) -> List[CommentInfo]:
        """Analyze comments in code content.

        Args:
            content: Code content to analyze

        Returns:
            List of CommentInfo objects
        """
        comments = []
        try:
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith("#"):
                    comments.append(
                        CommentInfo(
                            content=line[1:].strip(), line_number=i, is_inline=False
                        )
                    )
                elif "#" in line:
                    comments.append(
                        CommentInfo(
                            content=line[line.index("#") + 1 :].strip(),
                            line_number=i,
                            is_inline=True,
                        )
                    )
        except Exception as e:
            self.logger.error("Error analyzing comments: %s", str(e))
        return comments

    def _analyze_docstring(self, docstring: str) -> DocstringInfo:
        """Analyze a docstring.

        Args:
            docstring: Docstring content

        Returns:
            DocstringInfo object
        """
        if docstring.startswith('"""'):
            style = "google"
        elif docstring.startswith("'''"):
            style = "numpy"
        else:
            style = "plain"

        has_args = bool(re.search(r"Args:|Parameters:", docstring))
        has_returns = bool(re.search(r"Returns:|Return:", docstring))
        has_raises = bool(re.search(r"Raises:|Exceptions:", docstring))

        return DocstringInfo(
            content=docstring,
            style=style,
            line_count=len(docstring.splitlines()),
            has_args=has_args,
            has_returns=has_returns,
            has_raises=has_raises,
        )

    def analyze_documentation(self, content: str) -> DocumentationAnalysis:
        """Analyze documentation in code content.

        Args:
            content: Code content to analyze

        Returns:
            DocumentationAnalysis object
        """
        try:
            tree = ast.parse(content)
            total_nodes = 0
            documented_nodes = 0

            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                    total_nodes += 1
                    if ast.get_docstring(node):
                        documented_nodes += 1

            docstrings = self.analyze_docstrings(content)
            comments = self.analyze_comments(content)
            total_lines = len(content.splitlines())

            doc_coverage = documented_nodes / total_nodes if total_nodes > 0 else 0
            style_consistency = self._calculate_style_consistency(docstrings)
            quality_score = self._calculate_quality_score(docstrings, doc_coverage)

            return DocumentationAnalysis(
                docstrings=docstrings,
                comments=comments,
                total_lines=total_lines,
                doc_coverage=doc_coverage,
                style_consistency=style_consistency,
                quality_score=quality_score,
            )
        except Exception as e:
            self.logger.error("Error analyzing documentation: %s", str(e))
            return DocumentationAnalysis(
                docstrings=[],
                comments=[],
                total_lines=0,
                doc_coverage=0.0,
                style_consistency=0.0,
                quality_score=0.0,
            )

    def _calculate_style_consistency(self, docstrings: List[DocstringInfo]) -> float:
        """Calculate docstring style consistency score.

        Args:
            docstrings: List of DocstringInfo objects

        Returns:
            Style consistency score between 0 and 1
        """
        if not docstrings:
            return 0.0

        styles = [d.style for d in docstrings]
        dominant_style = max(set(styles), key=styles.count)
        consistent_count = sum(1 for s in styles if s == dominant_style)

        return consistent_count / len(styles)

    def _calculate_quality_score(
        self, docstrings: List[DocstringInfo], coverage: float
    ) -> float:
        """Calculate overall documentation quality score.

        Args:
            docstrings: List of DocstringInfo objects
            coverage: Documentation coverage score

        Returns:
            Quality score between 0 and 1
        """
        if not docstrings:
            return 0.0

        completeness = sum(1 for d in docstrings if d.has_args and d.has_returns) / len(
            docstrings
        )
        avg_length = sum(d.line_count for d in docstrings) / len(docstrings)
        length_score = min(avg_length / 5, 1.0)  # Normalize to max of 5 lines

        return (coverage + completeness + length_score) / 3

    def analyze(self, files: List[str]) -> Dict:
        """Analyze documentation in the given files.

        Args:
            files: List of file paths to analyze.

        Returns:
            Dict containing documentation analysis results.

        Raises:
            AnalysisError: If analysis fails.
        """
        try:
            self.metrics = DocumentationMetrics()

            for file_path in files:
                self._analyze_file(file_path)

            if self.metrics.total_files > 0:
                self.metrics.coverage_score = (
                    self.metrics.documented_files / self.metrics.total_files
                    + self.metrics.documented_functions
                    / max(self.metrics.total_functions, 1)
                    + self.metrics.documented_classes
                    / max(self.metrics.total_classes, 1)
                ) / 3

            return {"metrics": self.metrics.__dict__, "status": "success", "errors": []}

        except Exception as e:
            raise AnalysisError(f"Documentation analysis failed: {str(e)}")

    def _analyze_file(self, file_path: str) -> None:
        """Analyze documentation in a single file.

        Args:
            file_path: Path to the file to analyze.
        """
        # TODO: Implement file analysis
        pass
