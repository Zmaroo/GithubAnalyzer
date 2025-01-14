"""Documentation parser implementation."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ....models.analysis.ast import ParseResult
from ....models.core.errors import ParserError
from .base import BaseParser


class DocumentationParser(BaseParser):
    """Parser for code documentation."""

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the parser.

        Args:
            languages: Optional list of languages to initialize support for

        Raises:
            ParserError: If initialization fails
        """
        # No specific initialization needed for documentation parsing
        pass

    def parse(self, content: str, language: str) -> ParseResult:
        """Parse documentation content.

        Args:
            content: Content to parse
            language: Language identifier for the content

        Returns:
            ParseResult containing documentation information

        Raises:
            ParserError: If parsing fails
        """
        try:
            docstrings = self._extract_docstrings(content)
            comments = self._extract_comments(content)

            return ParseResult(
                ast=None,  # Documentation parser doesn't produce an AST
                language=language,
                is_valid=True,  # Documentation is always considered valid
                line_count=len(content.splitlines()),
                node_count=len(docstrings) + len(comments),
                errors=[],
                metadata={
                    "type": "documentation",
                    "docstrings": docstrings,
                    "comments": comments,
                    "doc_coverage": self._calculate_coverage(
                        content, docstrings, comments
                    ),
                },
            )
        except Exception as e:
            raise ParserError(f"Failed to parse documentation: {str(e)}")

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a file.

        Args:
            file_path: Path to the file to parse

        Returns:
            ParseResult containing documentation information

        Raises:
            ParserError: If file cannot be read or parsed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ParserError(f"File {file_path} not found")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Use file extension as language identifier
            language = file_path.suffix.lstrip(".")
            if not language:
                language = "text"

            result = self.parse(content, language)
            result.metadata["file_path"] = str(file_path)
            return result
        except Exception as e:
            raise ParserError(f"Failed to parse file {file_path}: {str(e)}")

    def cleanup(self) -> None:
        """Clean up parser resources."""
        # No cleanup needed for documentation parser
        pass

    def _extract_docstrings(self, content: str) -> List[Dict[str, Any]]:
        """Extract docstrings from content.

        Args:
            content: Content to extract docstrings from

        Returns:
            List of docstring information dictionaries
        """
        docstrings = []
        pattern = r'"""(.*?)"""'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            docstrings.append(
                {
                    "content": match.group(1).strip(),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        return docstrings

    def _extract_comments(self, content: str) -> List[Dict[str, Any]]:
        """Extract comments from content.

        Args:
            content: Content to extract comments from

        Returns:
            List of comment information dictionaries
        """
        comments = []
        pattern = r"#(.*?)$"

        for i, line in enumerate(content.splitlines(), 1):
            match = re.search(pattern, line)
            if match:
                comments.append({"content": match.group(1).strip(), "line": i})

        return comments

    def _calculate_coverage(
        self,
        content: str,
        docstrings: List[Dict[str, Any]],
        comments: List[Dict[str, Any]],
    ) -> float:
        """Calculate documentation coverage.

        Args:
            content: Original content
            docstrings: Extracted docstrings
            comments: Extracted comments

        Returns:
            Documentation coverage percentage
        """
        total_lines = len(content.splitlines())
        if total_lines == 0:
            return 0.0

        doc_lines = sum(len(d["content"].splitlines()) for d in docstrings)
        comment_lines = len(comments)

        return (doc_lines + comment_lines) / total_lines * 100
