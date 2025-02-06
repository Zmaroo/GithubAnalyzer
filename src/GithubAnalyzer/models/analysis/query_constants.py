"""Constants for tree-sitter query operations."""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Pattern types
PATTERN_TYPE_QUERY = "query"
PATTERN_TYPE_COMMON = "common"
PATTERN_TYPE_INTERFACE = "interface"
PATTERN_TYPE_FUNCTION = "function"
PATTERN_TYPE_CLASS = "class"
PATTERN_TYPE_CONTROL_FLOW = "control_flow"
PATTERN_TYPE_JS_TS = "js_ts"
PATTERN_TYPE_LANGUAGE_SPECIFIC = "language_specific"

# Pattern categories
PATTERN_CATEGORY_FUNCTION = "function"
PATTERN_CATEGORY_CLASS = "class"
PATTERN_CATEGORY_METHOD = "method"
PATTERN_CATEGORY_INTERFACE = "interface"
PATTERN_CATEGORY_CONTROL_FLOW = "control_flow"
PATTERN_CATEGORY_IMPORT = "import"
PATTERN_CATEGORY_STRUCT = "struct"
PATTERN_CATEGORY_NAMESPACE = "namespace"
PATTERN_CATEGORY_COMMENT = "comment"
PATTERN_CATEGORY_STRING = "string"
PATTERN_CATEGORY_ERROR = "error"

# Default node types by language
DEFAULT_NODE_TYPES = {
    'python': {
        'identifier': 'identifier',
        'formal_parameters': 'parameters',
        'statement_block': 'block',
        'class_body': 'block'
    },
    'javascript': {
        'identifier': 'identifier',
        'formal_parameters': 'formal_parameters',
        'statement_block': 'statement_block',
        'class_body': 'class_body'
    },
    'typescript': {
        'identifier': 'identifier',
        'formal_parameters': 'formal_parameters',
        'statement_block': 'statement_block',
        'class_body': 'class_body'
    },
    'java': {
        'identifier': 'identifier',
        'formal_parameters': 'formal_parameters',
        'statement_block': 'block',
        'class_body': 'class_body'
    }
}

# Default pattern configurations
DEFAULT_FUNCTION_CONFIG = {
    'name_type': 'identifier',
    'params_type': 'formal_parameters',
    'body_type': 'statement_block'
}

DEFAULT_CLASS_CONFIG = {
    'name_type': 'identifier',
    'body_type': 'class_body',
    'inheritance': ''
}

DEFAULT_METHOD_CONFIG = {
    'name_type': 'identifier',
    'params_type': 'formal_parameters',
    'body_type': 'statement_block'
}

# Pattern template keys
TEMPLATE_FUNCTION = "basic_function"
TEMPLATE_CLASS = "basic_class"
TEMPLATE_METHOD = "basic_method" 