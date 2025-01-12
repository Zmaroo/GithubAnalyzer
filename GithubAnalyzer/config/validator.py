"""Configuration validation"""
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import os

@dataclass
class ValidationRule:
    """Configuration validation rule"""
    field: str
    validator: callable
    message: str
    severity: str = "error"

class ConfigValidator:
    """Configuration validator"""
    
    @classmethod
    def validate_settings(cls, settings: Any) -> List[str]:
        """Validate settings dataclass"""
        errors = []
        
        # Validate paths exist or can be created
        for field_name, field_value in settings.__dict__.items():
            if isinstance(field_value, Path):
                try:
                    field_value.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Invalid path for {field_name}: {e}")
            
        # Validate numeric ranges
        if hasattr(settings, 'MAX_FILE_SIZE') and settings.MAX_FILE_SIZE <= 0:
            errors.append("MAX_FILE_SIZE must be positive")
            
        if hasattr(settings, 'BATCH_SIZE') and settings.BATCH_SIZE <= 0:
            errors.append("BATCH_SIZE must be positive")
            
        return errors

    @classmethod
    def validate_environment(cls) -> List[str]:
        """Validate environment configuration"""
        required_vars = {
            'PG_CONN_STRING': 'PostgreSQL connection string',
            'NEO4J_URI': 'Neo4j URI',
            'REDIS_HOST': 'Redis host'
        }
        
        errors = []
        for var, description in required_vars.items():
            if not os.getenv(var):
                errors.append(f"Missing {description} ({var})")
                
        return errors 