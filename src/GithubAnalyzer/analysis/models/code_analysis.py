"""Code analysis models."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

@dataclass
class CodeAnalysisResult:
    """Result of code analysis."""
    language: str
    node_count: int = 0
    metadata: Dict[str, Any] = None

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            'language': self.language,
            'node_count': self.node_count,
            'metadata': self.metadata or {}
        } 