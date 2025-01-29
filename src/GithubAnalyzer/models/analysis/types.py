"""Type definitions for tree-sitter analysis."""
from typing import Dict, List, Any
from tree_sitter import Node

# Common type aliases
LanguageId = str
QueryPattern = str
NodeDict = Dict[str, Any]
NodeList = List[Node]
QueryResult = Dict[str, NodeList] 