"""Operations service for core functionality."""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from .base_service import BaseService

if TYPE_CHECKING:
    from ..analysis.analyzer_service import AnalyzerService


class OperationsService(BaseService):
    """Service for core operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the operations service.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._analyzer: Optional["AnalyzerService"] = None
        self._initialized = False

    def initialize(self, analyzer: "AnalyzerService") -> None:
        """Initialize the operations service.

        Args:
            analyzer: Analyzer service instance
        """
        self._analyzer = analyzer
        self._initialized = True
        self.logger.info("Operations service initialized successfully")
