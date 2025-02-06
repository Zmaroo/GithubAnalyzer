"""JavaScript-specific Tree-sitter patterns."""

JS_VARIANT_PATTERNS = {
    "javascript": {
        # Basic pattern for function detection
        "function": """
            [
              (function_declaration)
              (function_expression)
              (arrow_function)
              (method_definition)
            ] @function
        """,
        # Extended pattern for detailed function information
        "function_details": """
            [
              (function_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body
                [
                  (comment)* @function.jsdoc
                ]) @function.def,
              (function_expression
                name: (identifier)? @function.name
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def,
              (arrow_function
                parameters: (formal_parameters) @function.params
                body: [
                  (statement_block) @function.body
                  (expression) @function.body
                ]) @function.def,
              (method_definition
                name: (property_identifier) @function.name
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def
            ]
        """,
        # Class patterns
        "class": """
            [
              (class_declaration)
              (class_expression)
            ] @class
        """,
        "class_details": """
            [
              (class_declaration
                name: (identifier) @class.name
                extends: (extends_clause
                  value: (identifier) @class.extends)? 
                body: (class_body
                  [
                    (method_definition)* @class.methods
                    (field_definition)* @class.fields
                    (static_block)* @class.static_blocks
                  ]
                  [
                    (comment)* @class.jsdoc
                  ]?)) @class.def,
              (class_expression
                name: (identifier)? @class.name
                extends: (extends_clause
                  value: (identifier) @class.extends)?
                body: (class_body)) @class.def
            ]
        """,
        # Module patterns
        "module": """
            (program
              [
                (comment)* @module.jsdoc
                (import_statement)* @module.imports
                (export_statement)* @module.exports
                (variable_declaration)* @module.declarations
                (class_declaration)* @module.classes
                (function_declaration)* @module.functions
              ]) @module
        """,
        "import": """
            [
              (import_statement
                source: (string) @import.source
                clause: [
                  (import_clause (identifier) @import.default)
                  (named_imports
                    (import_specifier
                      name: (identifier) @import.name
                      alias: (identifier)? @import.alias))
                ]) @import,
              (call_expression
                function: (identifier) @import.require
                (#eq? @import.require "require")
                arguments: (arguments (string) @import.source)) @import.require,
              (call_expression
                function: (import) @import.dynamic
                arguments: (arguments (string) @import.source)) @import.dynamic
            ]
        """,
        "variable": """
            (variable_declarator
               name: (identifier) @variable.name
               value: (_) @variable.value) @variable
        """,
        "conditional": """
            (if_statement
               condition: (parenthesized_expression)? @conditional.condition
               consequence: (block) @conditional.consequence
               (else_clause (block) @conditional.alternative)?) @conditional
        """,
        "loop": """
            [
              (for_statement
                (variable_declaration)? @loop.declaration
                body: (block) @loop.body),
              (while_statement
                condition: (parenthesized_expression)? @loop.condition
                body: (block) @loop.body)
            ] @loop
        """,
        "lambda": """
            (arrow_function
               parameters: (formal_parameters) @lambda.params
               body: [
                 (statement_block) @lambda.body
                 (expression) @lambda.body
               ]) @lambda
        """,
        "assignment": """
            (assignment_expression
               left: (identifier) @variable.name
               right: (_) @variable.value) @assignment
        """
    }
} 