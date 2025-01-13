"""Error models for the application"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class AnalysisError:
    """Base class for analysis errors"""
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None
    source: Optional[str] = None

@dataclass
class ParseError(AnalysisError):
    """Parser-specific errors"""
    line_number: Optional[int] = None
    column: Optional[int] = None
    snippet: Optional[str] = None

@dataclass
class DatabaseError(AnalysisError):
    """Database-related errors"""
    operation: Optional[str] = None
    connection_type: Optional[str] = None
    recoverable: bool = True

@dataclass
class ValidationError(AnalysisError):
    """Validation-related errors"""
    field: Optional[str] = None
    constraint: Optional[str] = None
    value: Optional[Any] = None

@dataclass
class SecurityError(AnalysisError):
    """Security-related errors"""
    severity: str = "high"
    vulnerability_type: Optional[str] = None
    recommendation: Optional[str] = None 