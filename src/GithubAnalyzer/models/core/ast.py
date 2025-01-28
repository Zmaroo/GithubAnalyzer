from dataclasses import dataclass
from tree_sitter import Tree, Node
"""AST models for tree-sitter parsing."""

from typing import Optional, List, Dict, Any

@dataclass
class ParseResult:
    """Result of parsing a file with tree-sitter."""
    tree: Optional[Tree]  # The tree-sitter parse tree
    language: str  # Language identifier
    functions: List[Dict[str, Node]] = None  # Function definitions with components
    classes: List[Dict[str, Node]] = None  # Class definitions with components
    imports: List[Dict[str, Node]] = None  # Import statements with components
    is_valid: bool = True  # Whether the parse tree is valid
    errors: List[str] = None  # List of error messages if any
    missing_nodes: List[Node] = None  # List of missing nodes
    error_nodes: List[Node] = None  # List of error nodes
    
    def __post_init__(self):
        """Initialize default values for optional fields."""
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
            
    def get_function_names(self) -> List[str]:
        """Get list of function names."""
        return [f['function.name'].text.decode('utf8') 
                for f in self.functions if 'function.name' in f]
                
    def get_class_names(self) -> List[str]:
        """Get list of class names."""
        return [c['class.name'].text.decode('utf8') 
                for c in self.classes if 'class.name' in c]
                
    def get_import_paths(self) -> List[str]:
        """Get list of imported module paths."""
        return [i['import.module'].text.decode('utf8') 
                for i in self.imports if 'import.module' in i]
                
    def get_error_locations(self) -> List[Dict[str, Any]]:
        """Get locations of syntax errors."""
        return [{
            'line': node.start_point[0] + 1,
            'column': node.start_point[1],
            'type': node.type
        } for node in self.error_nodes]
        
    def get_missing_locations(self) -> List[Dict[str, Any]]:
        """Get locations of missing nodes."""
        return [{
            'line': node.start_point[0] + 1,
            'column': node.start_point[1],
            'type': node.type
        } for node in self.missing_nodes]
        
    def has_syntax_errors(self) -> bool:
        """Check if there are any syntax errors."""
        return not self.is_valid or bool(self.error_nodes)
        
    def has_missing_nodes(self) -> bool:
        """Check if there are any missing required nodes."""
        return bool(self.missing_nodes)
        
    def get_structure(self) -> Dict[str, Any]:
        """Get high-level structure of the code."""
        return {
            'functions': self.get_function_names(),
            'classes': self.get_class_names(),
            'imports': self.get_import_paths(),
            'has_errors': self.has_syntax_errors(),
            'has_missing': self.has_missing_nodes()
        } 