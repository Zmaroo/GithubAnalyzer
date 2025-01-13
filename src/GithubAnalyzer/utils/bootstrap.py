"""Application bootstrap and initialization"""
from typing import Optional, Dict, Any, List
from pathlib import Path
from .registry import AnalysisToolRegistry
from .config import ConfigValidator
from .utils.logging import configure_logging
from .models.database import DatabaseConfig

class Bootstrap:
    """Application bootstrap handler"""
    
    @classmethod
    def initialize(cls, config_path: Optional[str] = None) -> AnalysisToolRegistry:
        """Initialize application"""
        # Configure logging first
        configure_logging()
        
        # Load and validate config
        errors = ConfigValidator.validate(config_path)
        if errors:
            cls._handle_config_errors(errors)
            
        # Initialize temp directories
        cls._init_directories()
        
        # Initialize services
        registry = AnalysisToolRegistry.create()
        
        return registry
        
    @classmethod
    def _init_directories(cls) -> None:
        """Initialize required directories"""
        dirs = ['temp', 'logs', 'cache']
        for dir_name in dirs:
            path = Path(dir_name)
            path.mkdir(exist_ok=True)
            
    @classmethod
    def _handle_config_errors(cls, errors: List[ConfigError]) -> None:
        """Handle configuration errors"""
        critical = [e for e in errors if e.severity == "error"]
        if critical:
            error_msg = "\n".join(f"- {e.path}: {e.message}" for e in critical)
            raise RuntimeError(f"Critical configuration errors:\n{error_msg}") 