"""Custom parsers for specialized language support."""
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

from GithubAnalyzer.models.core.parsers import (CustomParseResult,
                                                EditorConfigResult,
                                                EditorConfigSection,
                                                EnvFileResult,
                                                GitignorePattern,
                                                GitignoreResult,
                                                LockFileResult,
                                                RequirementSpec,
                                                RequirementsResult)
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class CustomParser(ABC):
    """Base class for custom file parsers."""
    _logger = logger
    _correlation_id: Optional[str] = None
    _operation_times: Dict[str, float] = field(default_factory=dict)
    _thread_local = threading.local()
    _start_time: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Initialize parser."""
        # Lazy import to avoid circular dependency
        from GithubAnalyzer.services.core.base_service import BaseService
        
        # Bind all required methods from BaseService
        if not hasattr(self, '_log'):
            self._log = BaseService._log.__get__(self)
        if not hasattr(self, '_get_context'):
            self._get_context = BaseService._get_context.__get__(self)
        if not hasattr(self, '_time_operation'):
            self._time_operation = BaseService._time_operation.__get__(self)
        if not hasattr(self, '_end_operation'):
            self._end_operation = BaseService._end_operation.__get__(self)
            
        self._log("debug", f"{self.__class__.__name__} initialized",
                operation="initialization")
    
    @abstractmethod
    def parse(self, content: str) -> Optional[CustomParseResult]:
        """Parse file content into a structured format.
        
        Args:
            content: Raw file content to parse
            
        Returns:
            CustomParseResult if successful, None otherwise
        """
        pass

@dataclass
class LockFileParser(CustomParser):
    """Parser for lock files (package-lock.json, Pipfile.lock, etc.)."""
    
    def parse(self, content: str) -> Optional[LockFileResult]:
        self._log("debug", "Parsing lock file",
                operation="file_parsing",
                content_length=len(content))
                
        try:
            # Try JSON first (most lock files are JSON)
            import json
            raw_data = json.loads(content)
            result = LockFileResult(
                raw_data=raw_data,
                format='json'
            )
            
            # Extract dependencies
            if 'dependencies' in raw_data:
                result.dependencies = raw_data['dependencies']
            if 'devDependencies' in raw_data:
                result.dev_dependencies = raw_data['devDependencies']
                
            self._log("debug", "Successfully parsed JSON lock file",
                    operation="file_parsing",
                    format="json")
            return result
            
        except json.JSONDecodeError:
            try:
                # Try YAML next (some lock files are YAML)
                import yaml
                raw_data = yaml.safe_load(content)
                result = LockFileResult(
                    raw_data=raw_data,
                    format='yaml'
                )
                
                # Extract dependencies
                if 'dependencies' in raw_data:
                    result.dependencies = raw_data['dependencies']
                if 'dev-dependencies' in raw_data:
                    result.dev_dependencies = raw_data['dev-dependencies']
                    
                self._log("debug", "Successfully parsed YAML lock file",
                        operation="file_parsing",
                        format="yaml")
                return result
                
            except yaml.YAMLError:
                try:
                    # Finally try TOML (Cargo.lock)
                    import toml
                    raw_data = toml.loads(content)
                    result = LockFileResult(
                        raw_data=raw_data,
                        format='toml'
                    )
                    
                    # Extract dependencies
                    if 'package' in raw_data:
                        for pkg in raw_data['package']:
                            if pkg.get('dependencies'):
                                result.dependencies.update(pkg['dependencies'])
                            if pkg.get('dev-dependencies'):
                                result.dev_dependencies.update(pkg['dev-dependencies'])
                                
                    self._log("debug", "Successfully parsed TOML lock file",
                            operation="file_parsing",
                            format="toml")
                    return result
                    
                except Exception as e:
                    self._log("error", "Failed to parse lock file",
                            operation="file_parsing",
                            error=str(e))
                    return None

@dataclass
class EnvFileParser(CustomParser):
    """Parser for .env files."""
    
    def parse(self, content: str) -> Optional[EnvFileResult]:
        self._log("debug", "Parsing env file",
                operation="file_parsing",
                content_length=len(content))
                
        try:
            result = EnvFileResult()
            
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('#'):
                    result.comments.append(line[1:].strip())
                elif '=' in line:
                    key, value = line.split('=', 1)
                    result.variables[key.strip()] = value.strip()
                    
            self._log("debug", "Successfully parsed env file",
                    operation="file_parsing",
                    variable_count=len(result.variables))
            return result
            
        except Exception as e:
            self._log("error", "Failed to parse env file",
                    operation="file_parsing",
                    error=str(e))
            return None

@dataclass
class RequirementsParser(CustomParser):
    """Parser for requirements.txt files."""
    
    def parse(self, content: str) -> Optional[RequirementsResult]:
        self._log("debug", "Parsing requirements file",
                operation="file_parsing",
                content_length=len(content))
                
        try:
            result = RequirementsResult()
            
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Handle editable installs
                is_editable = line.startswith('-e ')
                if is_editable:
                    line = line[3:].strip()
                    
                # Parse requirement
                if '>=' in line:
                    name, version = line.split('>=', 1)
                    spec = RequirementSpec(
                        name=name.strip(),
                        version=f'>={version.strip()}',
                        is_editable=is_editable
                    )
                elif '==' in line:
                    name, version = line.split('==', 1)
                    spec = RequirementSpec(
                        name=name.strip(),
                        version=f'=={version.strip()}',
                        is_editable=is_editable
                    )
                elif '<=' in line:
                    name, version = line.split('<=', 1)
                    spec = RequirementSpec(
                        name=name.strip(),
                        version=f'<={version.strip()}',
                        is_editable=is_editable
                    )
                else:
                    spec = RequirementSpec(
                        name=line,
                        version='latest',
                        is_editable=is_editable
                    )
                    
                # Add to appropriate list
                if line.startswith('-c '):
                    result.constraints.append(spec)
                else:
                    result.requirements.append(spec)
                    
            self._log("debug", "Successfully parsed requirements file",
                    operation="file_parsing",
                    requirement_count=len(result.requirements))
            return result
            
        except Exception as e:
            self._log("error", "Failed to parse requirements file",
                    operation="file_parsing",
                    error=str(e))
            return None

@dataclass
class GitignoreParser(CustomParser):
    """Parser for .gitignore files."""
    
    def parse(self, content: str) -> Optional[GitignoreResult]:
        self._log("debug", "Parsing gitignore file",
                operation="file_parsing",
                content_length=len(content))
                
        try:
            result = GitignoreResult()
            
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                pattern = GitignorePattern(
                    pattern=line.lstrip('!'),
                    negated=line.startswith('!'),
                    directory_only=line.endswith('/')
                )
                result.patterns.append(pattern)
                    
            self._log("debug", "Successfully parsed gitignore file",
                    operation="file_parsing",
                    pattern_count=len(result.patterns))
            return result
            
        except Exception as e:
            self._log("error", "Failed to parse gitignore file",
                    operation="file_parsing",
                    error=str(e))
            return None

@dataclass
class EditorConfigParser(CustomParser):
    """Parser for .editorconfig files."""
    
    def parse(self, content: str) -> Optional[EditorConfigResult]:
        self._log("debug", "Parsing editorconfig file",
                operation="file_parsing",
                content_length=len(content))
                
        try:
            result = EditorConfigResult()
            current_section: Optional[EditorConfigSection] = None
            
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if line.startswith('[') and line.endswith(']'):
                    if current_section:
                        result.sections.append(current_section)
                    glob_pattern = line[1:-1]
                    current_section = EditorConfigSection(glob_pattern=glob_pattern)
                    
                elif current_section and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle special case for root
                    if key == 'root' and value.lower() == 'true':
                        result.root = True
                        continue
                        
                    # Convert values to appropriate types
                    if key in {'indent_size', 'tab_width', 'max_line_length'}:
                        value = int(value) if value.isdigit() else None
                    elif key in {'trim_trailing_whitespace', 'insert_final_newline'}:
                        value = value.lower() == 'true'
                        
                    setattr(current_section, key, value)
                    
            # Add last section
            if current_section:
                result.sections.append(current_section)
                    
            self._log("debug", "Successfully parsed editorconfig file",
                    operation="file_parsing",
                    section_count=len(result.sections))
            return result
            
        except Exception as e:
            self._log("error", "Failed to parse editorconfig file",
                    operation="file_parsing",
                    error=str(e))
            return None

def get_custom_parser(file_path: Union[str, Path]) -> Optional[CustomParser]:
    """Get appropriate parser for a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        CustomParser instance if supported, None otherwise
    """
    path = Path(file_path)
    filename = path.name.lower()
    
    # Map filenames to parser classes
    parser_map = {
        'package-lock.json': LockFileParser,
        'yarn.lock': LockFileParser,
        'pipfile.lock': LockFileParser,
        'cargo.lock': LockFileParser,
        '.env': EnvFileParser,
        'requirements.txt': RequirementsParser,
        'constraints.txt': RequirementsParser,
        '.gitignore': GitignoreParser,
        '.dockerignore': GitignoreParser,
        '.editorconfig': EditorConfigParser
    }
    
    parser_class = parser_map.get(filename)
    if parser_class:
        return parser_class()
    return None 