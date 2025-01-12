"""Service layer for business logic"""
from __future__ import annotations
from typing import TYPE_CHECKING

from .base_service import BaseService, ServiceContext

if TYPE_CHECKING:
    from .parser_service import ParserService
    from .analyzer_service import AnalyzerService
    from .database_service import DatabaseService
    from .framework_service import FrameworkService
    from .graph_analysis_service import GraphAnalysisService

__all__ = [
    'BaseService',
    'ServiceContext',
    'ParserService',
    'AnalyzerService',
    'DatabaseService',
    'FrameworkService',
    'GraphAnalysisService'
]

# Import services after type checking to avoid circular imports
from .parser_service import ParserService
from .analyzer_service import AnalyzerService
from .database_service import DatabaseService
from .framework_service import FrameworkService
from .graph_analysis_service import GraphAnalysisService 