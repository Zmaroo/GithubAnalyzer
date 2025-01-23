"""Tree-sitter models."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from tree_sitter import Node

from src.GithubAnalyzer.core.models.errors import ParserError, QueryError

def get_node_text(node: Optional[Node], content: str) -> str:
    """Get text from a node."""
    if not node:
        return ""
    return content[node.start_byte:node.end_byte]

def node_to_dict(node: Node, include_metadata: bool = False) -> Dict[str, Any]:
    """Convert node to dictionary representation."""
    result = {
        'type': node.type,
        'children': [node_to_dict(child, include_metadata) for child in node.children]
    }
    
    if include_metadata:
        result.update({
            'start_point': node.start_point,
            'end_point': node.end_point
        })
    
    return result

def format_error_context(code: str, position: int, context_lines: int = 3) -> str:
    """Format error context from a position in code."""
    if position >= len(code):
        return code
        
    lines = code.split('\n')
    line_no = 0
    pos = 0
    
    # Find the line number containing the position
    for i, line in enumerate(lines):
        if pos + len(line) + 1 > position:
            line_no = i
            break
        pos += len(line) + 1
    
    # Calculate the column number
    col_no = position - pos
    
    # Get context lines
    start = max(0, line_no - context_lines)
    end = min(len(lines), line_no + context_lines + 1)
    
    # Format output with line numbers and pointer
    result = []
    for i in range(start, end):
        result.append(f"{i+1:>3} | {lines[i]}")
        if i == line_no:
            result.append("    " + " " * col_no + "^")
            result.append("")  # Add blank line after pointer
    
    return '\n'.join(result[:-1] if not result else result)  # Remove trailing empty line if it exists

def count_nodes(node: Optional[Node]) -> int:
    """Count total nodes in a tree starting from given node."""
    if not node:
        return 0
    return 1 + sum(count_nodes(child) for child in node.children) 