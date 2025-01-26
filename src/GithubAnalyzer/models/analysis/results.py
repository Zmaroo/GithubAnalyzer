from dataclasses import dataclass
"""Analysis result models."""
from typing import Dict, List, Any, Optional

@dataclass
class AnalysisResult:
    """Result of code analysis."""
    language: str
    file_path: str
    node_count: int = 0
    metadata: Dict[str, Any] = None

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            'language': self.language,
            'file_path': self.file_path,
            'node_count': self.node_count,
            'metadata': self.metadata or {}
        } 