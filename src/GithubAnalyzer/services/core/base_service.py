"""Base service class for all services."""
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class BaseService(BaseModel):
    """Base class for all services."""
    _logger = logger
    _correlation_id: Optional[str] = None
    _operation_times: Dict[str, float] = field(default_factory=dict)
    _thread_local = threading.local()
    _start_time: float = field(default_factory=time.time)

    def __post_init__(self):
        """Initialize base service."""
        super().__post_init__()
        self._log("debug", "Service initialized")

    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standard context for logging.
        
        Args:
            **kwargs: Additional context key-value pairs
            
        Returns:
            Dict containing standard context fields
        """
        context = {
            "correlation_id": self._correlation_id,
            "module": self.__class__.__module__,
            "component": self.__class__.__name__,
            "thread": threading.current_thread().name,
            **kwargs
        }
        
        # Add operation duration if available
        if hasattr(self._thread_local, "current_operation"):
            context["operation"] = self._thread_local.current_operation
            if self._thread_local.current_operation in self._operation_times:
                context["duration_ms"] = self._operation_times[self._thread_local.current_operation]
                
        return context

    def _log(self, level: str, message: str, **kwargs):
        """Log a message with standard context.
        
        Args:
            level: Log level (debug, info, warning, error)
            message: Log message
            **kwargs: Additional context key-value pairs
        """
        context = self._get_context(**kwargs)
        getattr(self._logger, level)(message, extra={"context": context})

    def _time_operation(self, operation: str):
        """Start timing an operation.
        
        Args:
            operation: Name of operation to time
        """
        self._thread_local.current_operation = operation
        self._thread_local.start_time = time.time()
        self._log("debug", f"Starting operation: {operation}")

    def _end_operation(self):
        """End timing the current operation."""
        if hasattr(self._thread_local, "current_operation"):
            operation = self._thread_local.current_operation
            duration = (time.time() - self._thread_local.start_time) * 1000
            self._operation_times[operation] = duration
            self._log("debug", f"Completed operation: {operation}", duration_ms=duration)
            delattr(self._thread_local, "current_operation")
            delattr(self._thread_local, "start_time")

    def get_operation_times(self) -> Dict[str, float]:
        """Get dictionary of operation times.
        
        Returns:
            Dict mapping operation names to durations in milliseconds
        """
        return self._operation_times.copy()

    @property
    def correlation_id(self) -> Optional[str]:
        """Get correlation ID for this service instance.
        
        Returns:
            Correlation ID string if set, None otherwise
        """
        return self._correlation_id 