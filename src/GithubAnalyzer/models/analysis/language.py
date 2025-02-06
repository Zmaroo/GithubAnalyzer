"""Language-related models for code analysis."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.models.core.language import LanguageFeatures, LanguageInfo


@dataclass
class LanguageDetectionResult(BaseModel):
    """Result of language detection."""
    file_path: str
    language: str
    confidence: float = 1.0
    is_supported: bool = True
    features: Optional[LanguageFeatures] = None
    errors: List[str] = field(default_factory=list)

@dataclass
class LanguagePattern(BaseModel):
    """A language-specific pattern."""
    pattern: str
    name: str
    language: str
    type: str = "language"
    is_optimized: bool = False

@dataclass
class LanguageIndicator(BaseModel):
    """An indicator for language detection."""
    name: str
    pattern: str
    weight: float = 1.0
    is_regex: bool = False

@dataclass
class CodeAnalysis(BaseModel):
    """Analysis of code in a specific language."""
    language: str
    file_path: str
    content: str
    ast: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    features: Optional[LanguageFeatures] = None
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize code analysis."""
        super().__post_init__()
        if not self.features and self.language:
            self.features = LanguageFeatures(
                language=self.language,
                supports_classes=True,
                supports_interfaces=False,
                supports_generics=False,
                supports_async=False,
                supports_coroutines=False
            ) 