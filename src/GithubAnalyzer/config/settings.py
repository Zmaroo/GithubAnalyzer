"""Global application settings and configuration"""
from dataclasses import dataclass, field
from typing import Dict, Any, Set, List
from pathlib import Path

@dataclass(frozen=True)
class GlobalSettings:
    """Global application settings"""
    # Core settings
    DEBUG: bool = False
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Service settings
    SERVICE_SETTINGS: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'github_analyzer',
            'user': 'postgres',
            'password': 'postgres',
            'enable_ssl': True,
            'connection_pooling': True
        },
        'parser': {
            'max_file_size': 1048576,
            'require_type_hints': True
        },
        'analyzer': {
            'enable_security_checks': True,
            'enable_type_checking': True
        },
        'graph': {
            'check_gds_patterns': True,
            'validate_projections': True
        }
    })
    
    # Analysis settings
    ANALYSIS_SETTINGS: Dict[str, Any] = field(default_factory=lambda: {
        'max_file_size': 5 * 1024 * 1024,
        'supported_languages': ['python', 'javascript'],
        'excluded_patterns': ['__pycache__', '.git', 'venv'],
        'max_complexity': 100
    })

settings = GlobalSettings() 