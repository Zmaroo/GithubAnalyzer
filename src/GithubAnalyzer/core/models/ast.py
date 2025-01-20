"""Core AST models and types."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParseResult:
    """Result of parsing a file or content."""
    
    ast: Optional[Any]  # The AST if available
    language: str  # Language/format identifier
    is_valid: bool  # Whether parsing was successful
    line_count: int  # Number of lines parsed
    node_count: int  # Number of AST nodes
    errors: List[str] = field(default_factory=list)  # Any parsing errors
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata 