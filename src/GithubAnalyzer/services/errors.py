"""Service-specific errors"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ServiceError(Exception):
    """Base service error"""
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class DatabaseError(ServiceError):
    """Database operation errors"""
    pass

class GraphAnalysisError(ServiceError):
    """Graph analysis errors"""
    pass

class FileParsingError(ServiceError):
    """File parsing errors"""
    pass

class FrameworkError(ServiceError):
    """Framework detection errors"""
    pass

class AnalyzerError(ServiceError):
    """Code analysis errors"""
    pass 