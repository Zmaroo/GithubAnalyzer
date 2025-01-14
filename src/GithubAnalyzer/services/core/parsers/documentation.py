"""Documentation parser implementation."""

import re
from typing import Any, Dict, List

from ....models.core.errors import ParseError
from ....models.core.parse import ParseResult
from .base import BaseParser


class DocumentationParser(BaseParser):
    """Parser for code documentation."""

    def _validate_config(self) -> None:
        """Validate parser configuration."""
        # No specific config needed for documentation parsing
        pass

    def parse(self, content: str) -> ParseResult:
        """Parse documentation content.

        Args:
            content: Content to parse

        Returns:
            ParseResult containing documentation information

        Raises:
            ParseError: If parsing fails
        """
        try:
            docstrings = self._extract_docstrings(content)
            comments = self._extract_comments(content)

            return ParseResult(
                content=content,
                line_count=len(content.splitlines()),
                char_count=len(content),
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
            raise ParseError(f"Failed to parse documentation: {str(e)}")

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
