"""Application settings and configuration"""
from dataclasses import dataclass
from typing import Set, Dict, Any
from pathlib import Path

@dataclass(frozen=True)
class AnalysisSettings:
    """Analysis configuration settings"""
    SUPPORTED_EXTENSIONS: Set[str] = frozenset({'.py', '.js', '.ts', '.java', '.cpp', '.go'})
    EXCLUDE_PATTERNS: Set[str] = frozenset({'__pycache__', 'node_modules', '.git', 'venv', 'env'})
    MAX_FILE_SIZE: int = 1024 * 1024  # 1MB
    BATCH_SIZE: int = 100

@dataclass(frozen=True)
class CacheSettings:
    """Cache configuration settings"""
    DEFAULT_TTL: int = 3600
    CACHE_DIR: Path = Path('cache')
    MAX_MEMORY_MB: int = 512

@dataclass(frozen=True)
class LoggingSettings:
    """Logging configuration settings"""
    DEFAULT_LEVEL: str = "INFO"
    LOG_DIR: Path = Path('logs')
    MAX_SIZE_MB: int = 10
    BACKUP_COUNT: int = 5
    
settings = AnalysisSettings()
cache_settings = CacheSettings()
logging_settings = LoggingSettings() 