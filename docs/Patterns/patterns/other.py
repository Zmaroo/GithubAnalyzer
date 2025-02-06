"""Tree-sitter patterns for other programming languages."""

ADA_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (subprogram_body)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (subprogram_body
             (procedure_specification
                name: (identifier)? @function.name)
            body: (block) @function.body) @function.def,
          (subprogram_body
             (function_specification
                name: (identifier)? @function.name)
            body: (block) @function.body) @function.def
        ]
    """
}

HASKELL_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (function_declaration)
          (lambda_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (function_declaration
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
            body: (expression) @function.body) @function.def,
          (lambda_expression
             parameters: (parameter_list)? @function.params
            body: (expression) @function.body) @function.def
        ]
    """,
    "import": """
        (import_declaration 
            module: (module_name) @import.name) @import
    """
}

PERL_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (subroutine_definition)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (subroutine_definition
             name: (identifier) @function.name
            body: (block) @function.body) @function.def
        ]
    """
}

OBJECTIVEC_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (method_declaration)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (method_declaration
             receiver: (object)?
             selector: (selector) @function.name
             parameters: (parameter_list)? @function.params
            body: (compound_statement) @function.body) @function.def
        ]
    """
}

LUA_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (function_declaration)
          (local_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (function_declaration
             name: (identifier)? @function.name
             parameters: (parameter_list)? @function.params
            body: (block) @function.body) @function.def,
          (local_function
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
            body: (block) @function.body) @function.def
        ]
    """
}

GROOVY_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (method_declaration)
          (closure_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (method_declaration
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
            body: (block) @function.body) @function.def,
          (closure_expression
             parameters: (parameter_list)? @function.params
            body: (block) @function.body) @function.def
        ]
    """
}

RACKET_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (definition)
          (lambda_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (definition
             name: (identifier) @function.name
            body: (expression) @function.body) @function.def,
          (lambda_expression
             parameters: (list) @function.params
            body: (expression) @function.body) @function.def
        ]
    """
}

CLOJURE_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (defn_declaration)
          (anonymous_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (defn_declaration
             name: (symbol) @function.name
             parameters: (vector) @function.params
            body: (expression) @function.body) @function.def,
          (anonymous_function
             parameters: (vector) @function.params
            body: (expression) @function.body) @function.def
        ]
    """
}

SQUIRREL_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (function_declaration)
          (anonymous_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (function_declaration
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
            body: (block) @function.body) @function.def,
          (anonymous_function
             parameters: (parameter_list)? @function.params
            body: (block) @function.body) @function.def
        ]
    """
}

POWERSHELL_PATTERNS = {
    # Basic pattern for function detection
    "function": """
        [
          (function_definition)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """
        [
          (function_definition
             name: (identifier) @function.name
             parameters: (parameter_block)? @function.params
            body: (script_block) @function.body) @function.def
        ]
    """
} 