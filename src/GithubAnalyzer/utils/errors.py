"""Centralized error handling"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AnalysisError(Exception):
    """Base error class"""
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    source: Optional[str] = None

class ServiceError(AnalysisError):
    """Base service error"""
    pass

class DatabaseError(ServiceError):
    """Database errors"""
    pass

class ParserError(ServiceError):
    """Parser errors"""
    pass

class AnalyzerError(ServiceError):
    """Analyzer errors"""
    pass

class GraphError(ServiceError):
    """Graph analysis errors"""
    pass

class FrameworkError(ServiceError):
    """Framework detection errors"""
    pass 