"""Parser service for code analysis"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import ast
from tree_sitter import Language, Parser
from pathlib import Path
from .configurable import ConfigurableService, ParserConfig
from .errors import FileParsingError
from ..models.base import ParseResult, TreeSitterNode
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class ParserMetrics:
    """Parser performance metrics"""
    files_processed: int = 0
    total_lines: int = 0
    avg_parse_time: float = 0.0
    error_count: int = 0
    cache_hits: int = 0
    complexity_violations: int = 0

class ParserService(ConfigurableService):
    """Service for parsing and analyzing code files"""
    
    def __init__(self, registry=None, config: Optional[ParserConfig] = None):
        self.parsers: Dict[str, Parser] = {}
        self.languages: Dict[str, Language] = {}
        self.metrics = ParserMetrics()
        super().__init__(registry, config or ParserConfig())
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize parser service"""
        try:
            if config:
                self._update_config(config)
                
            # Initialize parsers for supported languages
            self._init_parsers()
            
            # Validate parser configurations
            if not self._validate_parser_setup():
                raise FileParsingError("Parser initialization failed")
                
        except Exception as e:
            raise FileParsingError(f"Failed to initialize parser service: {e}")

    def _init_parsers(self) -> None:
        """Initialize language parsers"""
        try:
            # Initialize tree-sitter parsers for each supported language
            for ext in self.service_config.supported_extensions:
                language = self._get_language_for_extension(ext)
                if language:
                    parser = Parser()
                    parser.set_language(language)
                    self.parsers[ext] = parser
                    
        except Exception as e:
            raise FileParsingError(f"Failed to initialize parsers: {e}")

    def _validate_parser_setup(self) -> bool:
        """Validate parser configuration"""
        try:
            # Check required parsers are initialized
            for ext in self.service_config.supported_extensions:
                if ext not in self.parsers:
                    logger.error(f"Missing parser for extension: {ext}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Parser validation failed: {e}")
            return False

    def _validate_requirements(self) -> bool:
        """Validate service requirements from cursorrules"""
        if not super()._validate_requirements():
            return False
            
        config = self.service_config
        
        # Check docstring requirement
        if config.require_docstrings and not hasattr(self, '_check_docstrings'):
            logger.error("Docstring checking required but not implemented")
            return False
            
        # Check complexity threshold
        if config.complexity_threshold <= 0:
            logger.error("Invalid complexity threshold")
            return False
            
        return True

    def parse_file(self, file_path: str, content: Optional[str] = None) -> ParseResult:
        """Parse a code file"""
        try:
            # Check file size limit
            if Path(file_path).stat().st_size > self.service_config.max_file_size:
                raise FileParsingError("File exceeds size limit")
                
            # Get appropriate parser
            ext = Path(file_path).suffix
            parser = self.parsers.get(ext)
            if not parser:
                raise FileParsingError(f"No parser available for {ext}")
                
            # Parse content
            tree = parser.parse(bytes(content, "utf8") if content else Path(file_path).read_bytes())
            
            # Convert to our AST format
            ast_node = self._convert_to_ast(tree.root_node)
            
            # Extract semantic information
            semantic_info = self._extract_semantic_info(ast_node)
            
            # Update metrics
            self.metrics.files_processed += 1
            
            return ParseResult(
                ast=ast_node,
                semantic=semantic_info,
                success=True
            )
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Failed to parse {file_path}: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                success=False,
                errors=[str(e)]
            )

    def _cleanup(self) -> None:
        """Cleanup parser resources"""
        try:
            self.parsers.clear()
            self.languages.clear()
        except Exception as e:
            logger.error(f"Failed to cleanup parser resources: {e}")

    def get_metrics(self) -> ParserMetrics:
        """Get parser metrics"""
        return self.metrics

    # ... additional helper methods ... 