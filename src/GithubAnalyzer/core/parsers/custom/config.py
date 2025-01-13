"""Configuration file parser"""
from pathlib import Path
import yaml
import json
import toml
from typing import Dict, Any
from ..base import BaseParser
from ...models import ParseResult

class ConfigParser(BaseParser):
    """Parser for configuration files"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = {'.yaml', '.yml', '.json', '.toml', '.ini'}
        self.parsers = {
            '.yaml': self._parse_yaml,
            '.yml': self._parse_yaml,
            '.json': self._parse_json,
            '.toml': self._parse_toml,
            '.ini': self._parse_ini
        }
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file can be parsed"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def parse(self, content: str) -> ParseResult:
        """Parse configuration content"""
        if not content.strip():
            return ParseResult(
                ast=None,
                semantic={},
                errors=["Empty content"],
                success=False
            )
            
        try:
            file_path = self.current_file
            if not file_path:
                return ParseResult(
                    ast=None,
                    semantic={},
                    errors=["No file path provided"],
                    success=False
                )
                
            extension = Path(file_path).suffix.lower()
            parser = self.parsers.get(extension)
            
            if not parser:
                return ParseResult(
                    ast=None,
                    semantic={},
                    errors=[f"No parser for extension {extension}"],
                    success=False
                )
                
            config_data = parser(content)
            return ParseResult(
                ast=config_data,
                semantic={
                    'type': 'config',
                    'format': extension[1:],  # Remove leading dot
                    'content': config_data
                },
                success=True
            )
            
        except Exception as e:
            return ParseResult(
                ast=None,
                semantic={},
                errors=[str(e)],
                success=False
            )
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """Parse YAML content"""
        return yaml.safe_load(content) or {}
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON content"""
        return json.loads(content)
    
    def _parse_toml(self, content: str) -> Dict[str, Any]:
        """Parse TOML content"""
        return toml.loads(content)
    
    def _parse_ini(self, content: str) -> Dict[str, Any]:
        """Parse INI content"""
        # Simple INI parser
        config = {}
        current_section = None
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                config[current_section] = {}
            elif '=' in line and current_section:
                key, value = line.split('=', 1)
                config[current_section][key.strip()] = value.strip()
                
        return config 