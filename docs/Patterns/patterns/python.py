"""Python-specific Tree-sitter patterns."""

PYTHON_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_definition)
          (lambda)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (function_definition
            name: (identifier) @function.name
            parameters: (parameters) @function.params
            body: (block) @function.body
            [
              (string) @function.docstring
            ]?) @function.def,
          (lambda
            parameters: (lambda_parameters)? @function.params
            body: (_) @function.body) @function.def
        ]
    """,
    # Class patterns
    "class": """\
        [
          (class_definition)
        ] @class
    """,
    "class_details": """\
        [
          (class_definition
            name: (identifier) @class.name
            [
              (argument_list
                (identifier)* @class.bases)
            ]?
            body: (block
              [
                (string) @class.docstring
                (function_definition)* @class.methods
                (expression_statement
                  (assignment) @class.field)*
              ])) @class.def
        ]
    """,
    # Module patterns
    "module": """\
        (module
          [
            (string) @module.docstring
            (import_statement|import_from_statement)* @module.imports
            (expression_statement
              (assignment))* @module.globals
            (class_definition)* @module.classes
            (function_definition)* @module.functions
          ]) @module
    """,
    # Type annotation patterns
    "type_annotation": """\
        [
          (type
            [
              (identifier) @type.name
              (subscript
                value: (identifier) @type.generic.base
                subscript: (identifier) @type.generic.param)
            ]) @type,
          (function_definition
            return_type: (type) @function.return_type)
        ]
    """,
    # Documentation patterns
    "documentation": """\
        [
          (string) @docstring
          (comment) @comment
        ]
    """,
    "import": """\
        [
          (import_statement) @import.stmt
          (import_from_statement) @import.stmt
        ] @import
    """,
    "assignment": """\
        (assignment
          left: (identifier) @variable.name
          right: (_) @variable.value) @assignment
    """,
    "control_flow": """\
        [
          (if_statement) @if_stmt
          (for_statement) @for_stmt
          (while_statement) @while_stmt
          (try_statement) @try_stmt
          (with_statement) @with_stmt
        ] @control_flow
    """,
    "decorator": """\
        (decorator
          name: (identifier) @decorator.name) @decorator
    """,
    "special_methods": """\
        [
            (class_definition
                body: (block
                    (function_definition
                        name: (identifier) @special_method.name
                        (#match? @special_method.name "^(__[a-z]+__)$")
                        parameters: (parameters) @special_method.params
                        body: (block) @special_method.body
                    )) @special_method.class) @special_method
        ]
    """
} 