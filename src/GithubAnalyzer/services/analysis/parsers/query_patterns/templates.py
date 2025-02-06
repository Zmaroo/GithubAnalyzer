"""Templates for common query patterns used in tree-sitter parsers.

This module exports:
    PATTERN_TEMPLATES and the functions:
        - create_function_pattern
        - create_class_pattern
        - create_method_pattern

Each create_*_pattern function accepts an optional configuration dictionary to override default node type identifiers.
"""

from typing import Dict, Optional

from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

# Default node types for pattern templates
DEFAULT_NODE_TYPES = {
    "function_type": "function_definition",
    "name_type": "identifier",
    "params_type": "parameters",
    "body_type": "block",
    "class_type": "class_definition",
    "inheritance_type": "base_clause",
    "method_type": "method_definition",
}

# Common patterns that can be used across languages
COMMON_PATTERNS = {
    "function_definition": "(function_definition) @function",
    "class_definition": "(class_definition) @class",
    "method_definition": "(method_definition) @method",
    "variable_declaration": "(variable_declaration) @variable",
    "import_statement": "(import_statement) @import",
}

# Interface patterns for languages that support them
COMMON_INTERFACE_PATTERNS = {
    "interface_definition": "(interface_declaration) @interface",
    "interface_method": "(method_signature) @interface.method",
    "interface_property": "(property_signature) @interface.property",
}

# Function-related patterns
COMMON_FUNCTION_DETAILS = {
    "function_name": "(function_definition name: (identifier) @function.name)",
    "function_params": "(function_definition parameters: (parameter_list) @function.params)",
    "function_body": "(function_definition body: (block) @function.body)",
    "function_return": "(return_statement) @function.return",
}

# Class-related patterns
COMMON_CLASS_DETAILS = {
    "class_name": "(class_definition name: (identifier) @class.name)",
    "class_inheritance": "(class_definition superclass: (identifier) @class.parent)",
    "class_body": "(class_definition body: (class_body) @class.body)",
    "class_method": "(method_definition) @class.method",
    "class_property": "(property_definition) @class.property",
}

# Control flow patterns
COMMON_CONTROL_FLOW = {
    "if_statement": "(if_statement) @control.if",
    "else_clause": "(else_clause) @control.else",
    "for_loop": "(for_statement) @control.for",
    "while_loop": "(while_statement) @control.while",
    "try_block": "(try_statement) @control.try",
    "catch_clause": "(catch_clause) @control.catch",
    "finally_clause": "(finally_clause) @control.finally",
}

# Default configurations for different pattern types
DEFAULT_FUNCTION_CONFIG = {
    "function_type": DEFAULT_NODE_TYPES["function_type"],
    "name_type": DEFAULT_NODE_TYPES["name_type"],
    "params_type": DEFAULT_NODE_TYPES["params_type"],
    "body_type": DEFAULT_NODE_TYPES["body_type"],
}

DEFAULT_CLASS_CONFIG = {
    "class_type": DEFAULT_NODE_TYPES["class_type"],
    "name_type": DEFAULT_NODE_TYPES["name_type"],
    "inheritance_type": DEFAULT_NODE_TYPES["inheritance_type"],
    "body_type": DEFAULT_NODE_TYPES["body_type"],
}

DEFAULT_METHOD_CONFIG = {
    "method_type": DEFAULT_NODE_TYPES["method_type"],
    "name_type": DEFAULT_NODE_TYPES["name_type"],
    "params_type": DEFAULT_NODE_TYPES["params_type"],
    "body_type": DEFAULT_NODE_TYPES["body_type"],
}

# Pattern templates for creating custom patterns
PATTERN_TEMPLATES = {
    "basic_function": """\
({function_type}
  name: ({name_type}) @function.name
  parameters: ({params_type}) @function.params
  body: ({body_type}) @function.body) @function.def
""",
    "basic_class": """\
({class_type}
  name: ({name_type}) @class.name
  {inheritance}
  body: ({body_type}) @class.body) @class.def
""",
    "basic_method": """\
({method_type}
  name: ({name_type}) @method.name
  parameters: ({params_type}) @method.params
  body: ({body_type}) @method.body) @method.def
""",
    # Common patterns that apply to most languages
    "comment": """
        [
          (comment) @comment.line
          (block_comment) @comment.block
        ] @comment
    """,
    "string": """
        [
          (string_literal) @string
          (raw_string_literal) @string.raw
        ] @string.any
    """,
    "error": """
        [
          (ERROR) @error.syntax
          (MISSING) @error.missing
          (_
            (#is? @error.incomplete incomplete)
            (#is-not? @error.incomplete complete)) @error
        ]
    """
}

def create_function_pattern(function_type: str, config: Optional[Dict[str, str]] = None) -> str:
    """Create a function pattern from the basic_function template with configurable node type identifiers.
    
    Args:
        function_type: Type of function node.
        config: Optional dictionary to override default node type values for function name, parameters, and body.
                Defaults are: name_type='identifier', params_type='formal_parameters', body_type='statement_block'.
                
    Returns:
        A formatted function pattern string.
    """
    logger.debug("Creating function pattern", extra={
        'context': {
            'operation': 'create_pattern',
            'pattern_type': 'function',
            'function_type': function_type,
            'config': config
        }
    })
    
    defaults = {
        'name_type': 'identifier',
        'params_type': 'formal_parameters',
        'body_type': 'statement_block'
    }
    if config:
        defaults.update(config)
        
    pattern = PATTERN_TEMPLATES["basic_function"].format(
        function_type=function_type,
        name_type=defaults["name_type"],
        params_type=defaults["params_type"],
        body_type=defaults["body_type"]
    )
    
    logger.debug("Function pattern created", extra={
        'context': {
            'operation': 'create_pattern',
            'pattern_type': 'function',
            'pattern': pattern
        }
    })
    
    return pattern

def create_class_pattern(class_type: str, config: Optional[Dict[str, str]] = None) -> str:
    """Create a class pattern from the basic_class template with configurable node type identifiers.
    
    Args:
        class_type: Type of class node.
        config: Optional dictionary to override default node type values for class name, body, and inheritance clause.
                Defaults are: name_type='identifier', body_type='class_body', inheritance=''.
                
    Returns:
        A formatted class pattern string.
    """
    logger.debug("Creating class pattern", extra={
        'context': {
            'operation': 'create_pattern',
            'pattern_type': 'class',
            'class_type': class_type,
            'config': config
        }
    })
    
    defaults = {
        'name_type': 'identifier',
        'body_type': 'class_body',
        'inheritance': ''
    }
    if config:
        defaults.update(config)
        
    pattern = PATTERN_TEMPLATES["basic_class"].format(
        class_type=class_type,
        name_type=defaults["name_type"],
        body_type=defaults["body_type"],
        inheritance=defaults["inheritance"]
    )
    
    logger.debug("Class pattern created", extra={
        'context': {
            'operation': 'create_pattern',
            'pattern_type': 'class',
            'pattern': pattern
        }
    })
    
    return pattern

def create_method_pattern(method_type: str, config: Optional[Dict[str, str]] = None) -> str:
    """Create a method pattern from the basic_method template with configurable node type identifiers.
    
    Args:
        method_type: The node type for the method (e.g., 'method_declaration').
        config: Optional dictionary to override default node type values for method name, parameters, and body.
                Defaults are: name_type='identifier', params_type='formal_parameters', body_type='statement_block'.
                
    Returns:
        A formatted method pattern string.
    """
    logger.debug("Creating method pattern", extra={
        'context': {
            'operation': 'create_pattern',
            'pattern_type': 'method',
            'method_type': method_type,
            'config': config
        }
    })
    
    defaults = {
        'name_type': 'identifier',
        'params_type': 'formal_parameters',
        'body_type': 'statement_block'
    }
    if config:
        defaults.update(config)
        
    pattern = PATTERN_TEMPLATES["basic_method"].format(
        method_type=method_type,
        name_type=defaults["name_type"],
        params_type=defaults["params_type"],
        body_type=defaults["body_type"]
    )
    
    logger.debug("Method pattern created", extra={
        'context': {
            'operation': 'create_pattern',
            'pattern_type': 'method',
            'pattern': pattern
        }
    })
    
    return pattern 