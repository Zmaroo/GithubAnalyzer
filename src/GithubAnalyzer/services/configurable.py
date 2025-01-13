"""Configurable service base class"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .base import BaseService
from ..di import DependencyContainer
from ..errors import ServiceError
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class ServiceRequirements:
    """Service requirements from cursorrules"""
    initialization: bool = True
    error_handling: bool = True
    logging: bool = True
    cleanup: bool = True
    config_validation: bool = True
    dependency_validation: bool = True

class ConfigurableService(BaseService):
    """Base class for configurable services"""
    
    def __init__(self, container: DependencyContainer, config: Dict[str, Any]):
        self._container = container
        self._config = config
        self._requirements = ServiceRequirements()
        self._metrics = {}
        self._health_check_enabled = config.get('health_check', {}).get('enabled', False)
        super().__init__() 