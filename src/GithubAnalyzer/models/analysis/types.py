"""Type definitions for code analysis."""
from typing import (Any, Dict, List, NewType, Optional, Set, Tuple, TypedDict,
                    Union)

from tree_sitter import Node

from GithubAnalyzer.models.analysis.query import \
    QueryResult as QueryResultClass
from GithubAnalyzer.models.core.types import (LanguageId, NodeDict, NodeList,
                                              NodeMap, NodeSet)

# Analysis-specific type aliases
QueryPattern = str  # Tree-sitter query pattern string
QueryResult = QueryResultClass  # Results from executing a query
QueryCapture = Dict[str, Node]  # Captured nodes from a query
QueryMatch = Dict[str, Union[str, Node]]  # Single query match result

# Analysis result types
AnalysisResult = Dict[str, Any]  # Generic analysis result
FunctionAnalysis = Dict[str, Any]  # Function analysis result
ClassAnalysis = Dict[str, Any]  # Class analysis result
ModuleAnalysis = Dict[str, Any]  # Module analysis result

# Collection types
PatternMap = Dict[str, QueryPattern]  # Map of pattern names to patterns
ResultMap = Dict[str, QueryResult]  # Map of query names to results

# Type definitions
AnalysisType = NewType('AnalysisType', str)  # Type of analysis to perform
QueryType = NewType('QueryType', str)  # Type of query to execute
PatternType = NewType('PatternType', str)  # Type of pattern to match
ResultType = NewType('ResultType', str)  # Type of result to return
MetricsType = NewType('MetricsType', str)  # Type of metrics to collect
StatsType = NewType('StatsType', str)  # Type of statistics to gather 