import json
import yaml
import toml
from pathlib import Path
from typing import Dict, Any
from ..base import BaseParser
from ...models.base import ParseResult
from ...utils.logging import setup_logger

logger = setup_logger(__name__)

class ConfigParser(BaseParser):
    """Parser for configuration files"""
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a config file"""
        path = Path(file_path)
        return path.suffix in {'.json', '.yaml', '.yml', '.toml', '.ini'} or \
               path.name in {'pyproject.toml', 'setup.cfg'}

    def parse(self, content: str) -> ParseResult:
        """Parse configuration file content"""
        try:
            path = Path(self.current_file)
            
            if path.suffix == '.json':
                data = json.loads(content)
            elif path.suffix in {'.yaml', '.yml'}:
                data = yaml.safe_load(content)
            elif path.suffix == '.toml' or path.name == 'pyproject.toml':
                data = toml.loads(content)
            else:
                # Basic INI-style parsing
                data = self._parse_ini(content)
                
            return ParseResult(
                ast=None,  # Config files don't need AST
                semantic={
                    'type': 'config',
                    'format': path.suffix.lstrip('.'),
                    'content': data
                },
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing config file {self.current_file}: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                errors=[str(e)],
                success=False
            )

    def _parse_ini(self, content: str) -> Dict[str, Any]:
        """Basic INI file parser"""
        result = {}
        current_section = None
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                result[current_section] = {}
            elif '=' in line and current_section is not None:
                key, value = line.split('=', 1)
                result[current_section][key.strip()] = value.strip()
                
        return result 