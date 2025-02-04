"""Templates for common query patterns used in tree-sitter parsers.

This module exports:
    PATTERN_TEMPLATES and the functions:
        - create_function_pattern
        - create_class_pattern
        - create_method_pattern

Each create_*_pattern function accepts an optional configuration dictionary to override default node type identifiers.
"""

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
"""
}

def create_function_pattern(function_type: str, config: dict = None) -> str:
    """Create a function pattern from the basic_function template with configurable node type identifiers.
    
    Args:
        function_type: Type of function node.
        config: Optional dictionary to override default node type values for function name, parameters, and body.
                Defaults are: name_type='identifier', params_type='formal_parameters', body_type='statement_block'.
                
    Returns:
        A formatted function pattern string.
    """
    defaults = {
        'name_type': 'identifier',
        'params_type': 'formal_parameters',
        'body_type': 'statement_block'
    }
    if config:
        defaults.update(config)
    return PATTERN_TEMPLATES["basic_function"].format(
        function_type=function_type,
        name_type=defaults["name_type"],
        params_type=defaults["params_type"],
        body_type=defaults["body_type"]
    )

def create_class_pattern(class_type: str, config: dict = None) -> str:
    """Create a class pattern from the basic_class template with configurable node type identifiers.
    
    Args:
        class_type: Type of class node.
        config: Optional dictionary to override default node type values for class name, body, and inheritance clause.
                Defaults are: name_type='identifier', body_type='class_body', inheritance=''.
                
    Returns:
        A formatted class pattern string.
    """
    defaults = {
        'name_type': 'identifier',
        'body_type': 'class_body',
        'inheritance': ''
    }
    if config:
        defaults.update(config)
    return PATTERN_TEMPLATES["basic_class"].format(
        class_type=class_type,
        name_type=defaults["name_type"],
        body_type=defaults["body_type"],
        inheritance=defaults["inheritance"]
    )

def create_method_pattern(method_type: str, config: dict = None) -> str:
    """Create a method pattern from the basic_method template with configurable node type identifiers.
    
    Args:
        method_type: The node type for the method (e.g., 'method_declaration').
        config: Optional dictionary to override default node type values for method name, parameters, and body.
                Defaults are: name_type='identifier', params_type='formal_parameters', body_type='statement_block'.
                
    Returns:
        A formatted method pattern string.
    """
    defaults = {
        'name_type': 'identifier',
        'params_type': 'formal_parameters',
        'body_type': 'statement_block'
    }
    if config:
        defaults.update(config)
    return PATTERN_TEMPLATES["basic_method"].format(
        method_type=method_type,
        name_type=defaults["name_type"],
        params_type=defaults["params_type"],
        body_type=defaults["body_type"]
    ) 