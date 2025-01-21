"""Base AST models for parser implementations."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


class NodeType(Enum):
    """Common node types across all parsers."""
    MODULE = "module"
    PROGRAM = "program"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    COMMENT = "comment"
    ERROR = "error"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class Position:
    """Position in source code."""
    line: int  # 1-indexed
    column: int  # 1-indexed
    offset: int  # byte offset


@dataclass
class Range:
    """Range in source code."""
    start: Position
    end: Position


@dataclass
class ParseError:
    """Base class for parser errors."""
    message: str
    range: Range
    error_type: str = "syntax"
    context: Optional[str] = None
    expected_symbols: Optional[List[str]] = None
    parent_type: Optional[str] = None
    sibling_types: Optional[List[str]] = None

    def get_error_context(self) -> str:
        """Get formatted error context."""
        context = []
        if self.context:
            context.append(f"near '{self.context}'")
        if self.expected_symbols:
            expected = ", ".join(self.expected_symbols[:5])
            if len(self.expected_symbols) > 5:
                expected += "..."
            context.append(f"expected one of: {expected}")
        if self.parent_type:
            context.append(f"inside {self.parent_type}")
        
        return " ".join(context) if context else "invalid syntax"

    def format_message(self) -> str:
        """Get formatted error message."""
        base = f"{self.error_type.title()} error at line {self.range.start.line}, column {self.range.start.column}"
        context = self.get_error_context()
        return f"{base}: {context}"


@dataclass
class ParseResult:
    """Base class for parser results."""
    language: str
    errors: List[ParseError]
    is_valid: bool
    node_count: int
    metadata: Dict[str, Any]

    @property
    def success(self) -> bool:
        """Whether parsing was successful."""
        return self.is_valid

    @property
    def has_critical_errors(self) -> bool:
        """Whether there are critical errors."""
        return any(err.error_type != "missing" for err in self.errors)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of parsing errors."""
        error_types = {}
        error_locations = []
        
        for error in self.errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            error_locations.append({
                'line': error.range.start.line,
                'column': error.range.start.column,
                'type': error.error_type,
                'message': error.format_message(),
                'context': error.get_error_context()
            })
            
        return {
            'total_errors': len(self.errors),
            'error_types': error_types,
            'has_critical_errors': self.has_critical_errors,
            'error_locations': error_locations
        } 