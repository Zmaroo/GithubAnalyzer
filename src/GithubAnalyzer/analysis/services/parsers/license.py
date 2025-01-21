"""License parser implementation."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.GithubAnalyzer.core.models.ast import ParseResult
from src.GithubAnalyzer.core.models.errors import ParserError
from src.GithubAnalyzer.core.models.file import FileInfo, FileType
from src.GithubAnalyzer.core.services.parsers.base import BaseParser
from src.GithubAnalyzer.common.services.cache_service import CacheService
from src.GithubAnalyzer.core.utils.context_manager import ContextManager
from src.GithubAnalyzer.core.utils.decorators import retry, timeout, timer


class LicenseParser(BaseParser):
    """Parser for software licenses."""

    LICENSE_PATTERNS = {
        "MIT": r"MIT License",
        "Apache": r"Apache License",
        "GPL": r"GNU General Public License",
        "BSD": r"BSD License",
        "ISC": r"ISC License",
        "Mozilla": r"Mozilla Public License",
    }

    def __init__(self):
        super().__init__()

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the parser.

        Args:
            languages: Optional list of languages to initialize support for

        Raises:
            ParserError: If initialization fails
        """
        # No specific initialization needed for license parsing
        pass

    def parse(self, content: str, language: str) -> ParseResult:
        """Parse license content.

        Args:
            content: Content to parse
            language: Language identifier for the content (ignored for licenses)

        Returns:
            ParseResult containing license information

        Raises:
            ParserError: If parsing fails
        """
        try:
            # Detect license type
            license_type = None
            for name, pattern in self.LICENSE_PATTERNS.items():
                if re.search(pattern, content, re.IGNORECASE):
                    license_type = name
                    break

            # Extract key information
            year_match = re.search(r"Copyright \(c\) (\d{4})", content)
            year = year_match.group(1) if year_match else None

            holder_match = re.search(r"Copyright \(c\) (?:\d{4} )?([^\n]+)", content)
            holder = holder_match.group(1).strip() if holder_match else None

            return ParseResult(
                ast=None,  # License parser doesn't produce an AST
                language="text",  # Licenses are always text
                is_valid=license_type is not None,
                line_count=len(content.splitlines()),
                node_count=1,  # License is treated as a single node
                errors=[] if license_type else ["Unknown license type"],
                metadata={
                    "type": "license",
                    "license_type": license_type,
                    "year": year,
                    "holder": holder,
                    "raw_content": content,
                },
            )
        except Exception as e:
            raise ParserError(f"Failed to parse license: {str(e)}")

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a license file.

        Args:
            file_path: Path to the file to parse

        Returns:
            ParseResult containing license information

        Raises:
            ParserError: If file cannot be read or parsed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ParserError(f"File {file_path} not found")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            result = self.parse(content, "text")
            result.metadata["file_path"] = str(file_path)
            return result
        except Exception as e:
            raise ParserError(f"Failed to parse file {file_path}: {str(e)}")

    def cleanup(self) -> None:
        """Clean up parser resources."""
        # No cleanup needed for license parser
        pass
