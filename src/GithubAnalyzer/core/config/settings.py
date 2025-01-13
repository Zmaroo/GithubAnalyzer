"""Global settings and configuration"""
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

@dataclass
class Settings:
    """Application settings"""
    # Performance settings
    max_workers: int = 4
    cache_ttl: int = 3600
    batch_size: int = 100
    memory_limit: int = 1024 * 1024 * 1024  # 1GB
    
    # Security settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set = None
    safe_paths: set = None
    
    # Database settings
    db_pool_size: int = 10
    db_timeout: int = 30
    
    def __post_init__(self):
        self.allowed_extensions = {'.py', '.js', '.java', '.go', '.rs'}
        self.safe_paths = {str(Path.cwd())}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            'max_workers': self.max_workers,
            'cache_ttl': self.cache_ttl,
            'batch_size': self.batch_size,
            'memory_limit': self.memory_limit,
            'max_file_size': self.max_file_size,
            'allowed_extensions': list(self.allowed_extensions),
            'safe_paths': list(self.safe_paths),
            'db_pool_size': self.db_pool_size,
            'db_timeout': self.db_timeout
        }

# Global settings instance
settings = Settings() 