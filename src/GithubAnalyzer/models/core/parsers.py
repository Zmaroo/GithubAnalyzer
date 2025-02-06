"""Core models for parsing project configuration files."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

ParserFunc = Callable[[str], Dict[str, Any]]

@dataclass
class CustomParseResult(BaseModel):
    """Base class for custom parser results."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize parse result."""
        super().__post_init__()
        self._log("debug", "Custom parse result initialized",
                is_valid=self.is_valid,
                error_count=len(self.errors),
                has_data=self.raw_data is not None)

@dataclass
class LockFileResult(CustomParseResult):
    """Result of parsing a lock file."""
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    format: str = 'unknown'  # json, yaml, or toml
    
    def __post_init__(self):
        """Initialize lock file result."""
        super().__post_init__()
        self._log("debug", "Lock file result initialized",
                dependency_count=len(self.dependencies),
                dev_dependency_count=len(self.dev_dependencies),
                format=self.format)

@dataclass
class EnvFileResult(CustomParseResult):
    """Result of parsing an env file."""
    variables: Dict[str, str] = field(default_factory=dict)
    comments: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize env file result."""
        super().__post_init__()
        self._log("debug", "Env file result initialized",
                variable_count=len(self.variables),
                comment_count=len(self.comments))

@dataclass
class RequirementSpec:
    """Specification for a Python requirement."""
    name: str
    version: str
    is_editable: bool = False
    extras: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        """Get string representation."""
        result = self.name
        if self.version != 'latest':
            result += self.version
        if self.extras:
            result += f"[{','.join(self.extras)}]"
        if self.is_editable:
            result = f"-e {result}"
        return result

@dataclass
class RequirementsResult(CustomParseResult):
    """Result of parsing a requirements file."""
    requirements: List[RequirementSpec] = field(default_factory=list)
    constraints: List[RequirementSpec] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize requirements result."""
        super().__post_init__()
        self._log("debug", "Requirements result initialized",
                requirement_count=len(self.requirements),
                constraint_count=len(self.constraints))

@dataclass
class GitignorePattern:
    """A pattern in a .gitignore file."""
    pattern: str
    negated: bool = False
    directory_only: bool = False
    
    def __str__(self) -> str:
        """Get string representation."""
        result = self.pattern
        if self.negated:
            result = f"!{result}"
        if self.directory_only and not result.endswith('/'):
            result += '/'
        return result

@dataclass
class GitignoreResult(CustomParseResult):
    """Result of parsing a .gitignore file."""
    patterns: List[GitignorePattern] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize gitignore result."""
        super().__post_init__()
        self._log("debug", "Gitignore result initialized",
                pattern_count=len(self.patterns))

@dataclass
class EditorConfigSection:
    """A section in an .editorconfig file."""
    glob_pattern: str
    indent_style: Optional[str] = None
    indent_size: Optional[int] = None
    tab_width: Optional[int] = None
    end_of_line: Optional[str] = None
    charset: Optional[str] = None
    trim_trailing_whitespace: Optional[bool] = None
    insert_final_newline: Optional[bool] = None
    max_line_length: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class EditorConfigResult(CustomParseResult):
    """Result of parsing an .editorconfig file."""
    sections: List[EditorConfigSection] = field(default_factory=list)
    root: bool = False
    
    def __post_init__(self):
        """Initialize editorconfig result."""
        super().__post_init__()
        self._log("debug", "Editorconfig result initialized",
                section_count=len(self.sections),
                is_root=self.root)

def get_custom_parser(file_path: str) -> Optional[ParserFunc]:
    """Get a custom parser for special file types.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Parser function if available, None otherwise
    """
    path = Path(file_path)
    filename = path.name.lower()
    
    # Add custom parsers for special files
    if filename in ['dockerfile', 'containerfile']:
        return parse_dockerfile
    elif filename == 'makefile':
        return parse_makefile
    elif filename in ['requirements.txt', 'constraints.txt']:
        return parse_requirements
    elif filename in ['.gitignore', '.dockerignore']:
        return parse_ignore_file
    
    return None

def parse_dockerfile(content: str) -> Dict[str, Any]:
    """Parse a Dockerfile."""
    # Basic Dockerfile parsing
    return {
        'type': 'dockerfile',
        'content': content,
        'is_valid': True
    }

def parse_makefile(content: str) -> Dict[str, Any]:
    """Parse a Makefile."""
    # Basic Makefile parsing
    return {
        'type': 'makefile',
        'content': content,
        'is_valid': True
    }

def parse_requirements(content: str) -> Dict[str, Any]:
    """Parse a requirements.txt file."""
    # Basic requirements.txt parsing
    return {
        'type': 'requirements',
        'content': content,
        'is_valid': True
    }

def parse_ignore_file(content: str) -> Dict[str, Any]:
    """Parse a .gitignore or .dockerignore file."""
    # Basic ignore file parsing
    return {
        'type': 'ignore',
        'content': content,
        'is_valid': True
    } 