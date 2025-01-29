"""Custom parsers for file types not supported by tree-sitter."""

from pathlib import Path
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import time
import threading
from GithubAnalyzer.utils.logging import get_logger

# Initialize logger
logger = get_logger("parsers.custom")

class CustomParser(ABC):
    """Base class for custom file parsers."""
    
    @abstractmethod
    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse file content into a structured format.
        
        Args:
            content: Raw file content to parse
            
        Returns:
            Dictionary containing parsed data if successful, None otherwise
        """
        pass

class LockFileParser(CustomParser):
    """Parser for lock files (package-lock.json, Pipfile.lock, etc.)."""
    
    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            # Try JSON first (most lock files are JSON)
            import json
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # Try YAML next (some lock files are YAML)
                import yaml
                return yaml.safe_load(content)
            except yaml.YAMLError:
                try:
                    # Finally try TOML (Cargo.lock)
                    import toml
                    return toml.loads(content)
                except:
                    return None

class EnvFileParser(CustomParser):
    """Parser for .env files."""
    
    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            result = {}
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        result[key.strip()] = value.strip()
            return result
        except Exception:
            return None

class RequirementsParser(CustomParser):
    """Parser for requirements.txt files."""
    
    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            requirements = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    if '>=' in line:
                        name, version = line.split('>=', 1)
                        requirements.append({
                            'name': name.strip(),
                            'version': f'>={version.strip()}'
                        })
                    elif '==' in line:
                        name, version = line.split('==', 1)
                        requirements.append({
                            'name': name.strip(),
                            'version': f'=={version.strip()}'
                        })
                    elif '<=' in line:
                        name, version = line.split('<=', 1)
                        requirements.append({
                            'name': name.strip(),
                            'version': f'<={version.strip()}'
                        })
                    else:
                        requirements.append({
                            'name': line,
                            'version': 'latest'
                        })
            return {'requirements': requirements}
        except Exception:
            return None

class GitignoreParser(CustomParser):
    """Parser for .gitignore files."""
    
    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            patterns = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append({
                        'pattern': line,
                        'negated': line.startswith('!'),
                        'directory_only': line.endswith('/')
                    })
            return {'patterns': patterns}
        except Exception:
            return None

class EditorConfigParser(CustomParser):
    """Parser for .editorconfig files."""
    
    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            sections = {}
            current_section = None
            
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    sections[current_section] = {}
                elif current_section and '=' in line:
                    key, value = line.split('=', 1)
                    sections[current_section][key.strip()] = value.strip()
                    
            return sections
        except Exception:
            return None

# Registry of custom parsers
CUSTOM_PARSERS = {
    # Lock files
    'package-lock.json': LockFileParser(),
    'yarn.lock': LockFileParser(),
    'Pipfile.lock': LockFileParser(),
    'poetry.lock': LockFileParser(),
    'Cargo.lock': LockFileParser(),
    'composer.lock': LockFileParser(),
    'pnpm-lock.yaml': LockFileParser(),
    
    # Environment files
    '.env': EnvFileParser(),
    '.env.local': EnvFileParser(),
    '.env.development': EnvFileParser(),
    '.env.test': EnvFileParser(),
    '.env.production': EnvFileParser(),
    '.env.example': EnvFileParser(),
    '.env.sample': EnvFileParser(),
    '.env.template': EnvFileParser(),
    
    # Python requirements
    'requirements.txt': RequirementsParser(),
    'requirements-dev.txt': RequirementsParser(),
    'requirements-test.txt': RequirementsParser(),
    'requirements-prod.txt': RequirementsParser(),
    'constraints.txt': RequirementsParser(),
    
    # Git files
    '.gitignore': GitignoreParser(),
    
    # Editor config
    '.editorconfig': EditorConfigParser()
}

def get_custom_parser(file_path: str) -> Optional[CustomParser]:
    """Get a custom parser for a file type.
    
    Args:
        file_path: Path to the file
        
    Returns:
        CustomParser instance if available, None otherwise
    """
    start_time = time.time()
    context = {
        'module': 'custom_parsers',
        'thread': threading.get_ident(),
        'duration_ms': 0,
        'file_path': file_path
    }
    
    # Check exact filename matches first
    filename = Path(file_path).name
    if filename in CUSTOM_PARSERS:
        parser = CUSTOM_PARSERS[filename]
        context['duration_ms'] = (time.time() - start_time) * 1000
        context['parser_type'] = parser.__class__.__name__
        logger.debug("Found custom parser by filename", extra={'context': context})
        return parser
        
    # Check extension matches
    extension = Path(file_path).suffix
    if extension in CUSTOM_PARSERS:
        parser = CUSTOM_PARSERS[extension]
        context['duration_ms'] = (time.time() - start_time) * 1000
        context['parser_type'] = parser.__class__.__name__
        logger.debug("Found custom parser by extension", extra={'context': context})
        return parser
        
    context['duration_ms'] = (time.time() - start_time) * 1000
    logger.debug("No custom parser found", extra={'context': context})
    return None 