from dataclasses import dataclass, field

from tree_sitter import Node, Tree

"""AST models for tree-sitter parsing."""

from typing import Any, Dict, List, Optional, Union

from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.models.core.types import (NodeDict, NodeList,
                                              TreeSitterRange)
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

def get_node_text(node: Node) -> str:
    """Get text for a node."""
    if not node:
        return ""
    try:
        return node.text.decode('utf8')
    except (AttributeError, UnicodeDecodeError):
        return str(node)

def get_node_type(node: Node) -> str:
    """Get type of a node."""
    if not node:
        return ""
    return node.type

def get_node_range(node: Node) -> TreeSitterRange:
    """Get range of a node."""
    if not node:
        return TreeSitterRange(
            start_point=(0, 0),
            end_point=(0, 0),
            start_byte=0,
            end_byte=0
        )
    return TreeSitterRange(
        start_point=node.start_point,
        end_point=node.end_point,
        start_byte=node.start_byte,
        end_byte=node.end_byte
    )

def is_valid_node(node: Node) -> bool:
    """Check if a node is valid."""
    return (
        node is not None and
        hasattr(node, 'type') and
        hasattr(node, 'has_error') and
        not node.has_error
    )

def node_to_dict(node: Node) -> NodeDict:
    """Convert a node to a dictionary."""
    if not node:
        return {}
    return {
        'type': node.type,
        'text': get_node_text(node),
        'start_point': node.start_point,
        'end_point': node.end_point,
        'start_byte': node.start_byte,
        'end_byte': node.end_byte,
        'children': [node_to_dict(child) for child in node.children]
    }

@dataclass
class ParseResult:
    """Result of parsing a file with tree-sitter."""
    tree: Optional[Tree]  # The tree-sitter parse tree
    language: str  # Language identifier
    metadata: Dict[str, Any] = None  # Metadata about the parsed file and its structure
    functions: List[Dict[str, Node]] = None  # Function definitions with components
    classes: List[Dict[str, Node]] = None  # Class definitions with components
    imports: List[Dict[str, Node]] = None  # Import statements with components
    is_supported: bool = True  # Whether the language is supported and parse tree is valid
    errors: List[str] = None  # List of error messages if any
    missing_nodes: List[Node] = None  # List of missing nodes
    error_nodes: List[Node] = None  # List of error nodes
    
    def __post_init__(self):
        """Initialize default values for optional fields."""
        logger.debug("Initializing parse result", extra={
            'context': {
                'operation': 'initialization',
                'language': self.language,
                'has_tree': self.tree is not None,
                'is_supported': self.is_supported
            }
        })
        
        if self.metadata is None:
            self.metadata = {}
        if self.functions is None:
            self.functions = []
        if self.classes is None:
            self.classes = []
        if self.imports is None:
            self.imports = []
        if self.errors is None:
            self.errors = []
        if self.missing_nodes is None:
            self.missing_nodes = []
        if self.error_nodes is None:
            self.error_nodes = []
            
        # Update metadata with parse results
        self.metadata.update({
            'functions': self.get_function_names(),
            'classes': self.get_class_names(),
            'imports': self.get_import_paths(),
            'has_errors': self.has_syntax_errors(),
            'has_missing': self.has_missing_nodes(),
            'is_supported': self.is_supported,
            'error_locations': self.get_error_locations(),
            'missing_locations': self.get_missing_locations()
        })
        
        logger.debug("Parse result initialized", extra={
            'context': {
                'operation': 'initialization',
                'function_count': len(self.functions),
                'class_count': len(self.classes),
                'import_count': len(self.imports),
                'error_count': len(self.errors),
                'missing_count': len(self.missing_nodes),
                'error_node_count': len(self.error_nodes)
            }
        })
            
    def get_function_names(self) -> List[str]:
        """Get list of function names."""
        names = [f['function.name'].text.decode('utf8') 
                for f in self.functions if 'function.name' in f]
        logger.debug("Retrieved function names", extra={
            'context': {
                'operation': 'get_function_names',
                'count': len(names)
            }
        })
        return names
                
    def get_class_names(self) -> List[str]:
        """Get list of class names."""
        names = [c['class.name'].text.decode('utf8') 
                for c in self.classes if 'class.name' in c]
        logger.debug("Retrieved class names", extra={
            'context': {
                'operation': 'get_class_names',
                'count': len(names)
            }
        })
        return names
                
    def get_import_paths(self) -> List[str]:
        """Get list of imported module paths."""
        paths = [i['import.module'].text.decode('utf8') 
                for i in self.imports if 'import.module' in i]
        logger.debug("Retrieved import paths", extra={
            'context': {
                'operation': 'get_import_paths',
                'count': len(paths)
            }
        })
        return paths
                
    def get_error_locations(self) -> List[Dict[str, Any]]:
        """Get locations of syntax errors."""
        locations = [{
            'line': node.start_point[0] + 1,
            'column': node.start_point[1],
            'type': node.type
        } for node in self.error_nodes]
        logger.debug("Retrieved error locations", extra={
            'context': {
                'operation': 'get_error_locations',
                'count': len(locations)
            }
        })
        return locations
        
    def get_missing_locations(self) -> List[Dict[str, Any]]:
        """Get locations of missing nodes."""
        locations = [{
            'line': node.start_point[0] + 1,
            'column': node.start_point[1],
            'type': node.type
        } for node in self.missing_nodes]
        logger.debug("Retrieved missing node locations", extra={
            'context': {
                'operation': 'get_missing_locations',
                'count': len(locations)
            }
        })
        return locations
        
    def has_syntax_errors(self) -> bool:
        """Check if there are any syntax errors."""
        has_errors = not self.is_supported or bool(self.error_nodes)
        logger.debug("Checked for syntax errors", extra={
            'context': {
                'operation': 'has_syntax_errors',
                'has_errors': has_errors,
                'is_supported': self.is_supported,
                'error_count': len(self.error_nodes)
            }
        })
        return has_errors
        
    def has_missing_nodes(self) -> bool:
        """Check if there are any missing required nodes."""
        has_missing = bool(self.missing_nodes)
        logger.debug("Checked for missing nodes", extra={
            'context': {
                'operation': 'has_missing_nodes',
                'has_missing': has_missing,
                'missing_count': len(self.missing_nodes)
            }
        })
        return has_missing
        
    def get_structure(self) -> Dict[str, Any]:
        """Get high-level structure of the code."""
        structure = {
            'functions': self.get_function_names(),
            'classes': self.get_class_names(),
            'imports': self.get_import_paths(),
            'has_errors': self.has_syntax_errors(),
            'has_missing': self.has_missing_nodes()
        }
        logger.debug("Retrieved code structure", extra={
            'context': {
                'operation': 'get_structure',
                'function_count': len(structure['functions']),
                'class_count': len(structure['classes']),
                'import_count': len(structure['imports']),
                'has_errors': structure['has_errors'],
                'has_missing': structure['has_missing']
            }
        })
        return structure 

@dataclass
class TreeSitterEdit(BaseModel):
    """Represents a tree-sitter edit operation."""
    start_byte: int
    old_end_byte: int
    new_end_byte: int
    start_point: tuple[int, int]
    old_end_point: tuple[int, int]
    new_end_point: tuple[int, int]

@dataclass
class TreeSitterBase(BaseModel):
    """Base class for tree-sitter operations."""
    _logger = logger
    _tree: Optional[Tree] = None
    _root: Optional[Node] = None
    _edits: List[TreeSitterEdit] = field(default_factory=list)

    def __post_init__(self):
        """Initialize tree-sitter base."""
        super().__post_init__()
        self._log("debug", "Tree-sitter base initialized")

    def get_node_text(self, node: Node) -> str:
        """Get text for a node.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            Text content of the node
        """
        return get_node_text(node)

    def get_node_type(self, node: Node) -> str:
        """Get type of a node.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            Type of the node
        """
        return get_node_type(node)

    def get_node_children(self, node: Node) -> NodeList:
        """Get children of a node.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            List of child nodes
        """
        if not node:
            return []
        return node.children

    def get_node_parent(self, node: Node) -> Optional[Node]:
        """Get parent of a node.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            Parent node if it exists, None otherwise
        """
        if not node:
            return None
        return node.parent

    def get_node_start_point(self, node: Node) -> tuple[int, int]:
        """Get start point of a node.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            Tuple of (row, column)
        """
        if not node:
            return (0, 0)
        return node.start_point

    def get_node_end_point(self, node: Node) -> tuple[int, int]:
        """Get end point of a node.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            Tuple of (row, column)
        """
        if not node:
            return (0, 0)
        return node.end_point

    def get_node_range(self, node: Node) -> TreeSitterRange:
        """Get range of a node.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            TreeSitterRange containing start and end points
        """
        if not node:
            return TreeSitterRange(
                start_point=(0, 0),
                end_point=(0, 0),
                start_byte=0,
                end_byte=0
            )
        return TreeSitterRange(
            start_point=node.start_point,
            end_point=node.end_point,
            start_byte=node.start_byte,
            end_byte=node.end_byte
        )

    def get_node_dict(self, node: Node) -> NodeDict:
        """Convert a node to a dictionary.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            Dictionary representation of the node
        """
        return node_to_dict(node)

    def get_root(self) -> Optional[Node]:
        """Get root node of the tree.
        
        Returns:
            Root node if tree exists, None otherwise
        """
        if not self._tree:
            return None
        return self._tree.root_node

    def get_tree(self) -> Optional[Tree]:
        """Get tree-sitter tree.
        
        Returns:
            Tree-sitter tree if it exists, None otherwise
        """
        return self._tree

    def add_edit(self, edit: TreeSitterEdit):
        """Add an edit operation.
        
        Args:
            edit: Tree-sitter edit operation
        """
        self._edits.append(edit)
        self._log("debug", "Added edit operation", edit=edit)

    def get_edits(self) -> List[TreeSitterEdit]:
        """Get list of edit operations.
        
        Returns:
            List of tree-sitter edit operations
        """
        return self._edits.copy() 