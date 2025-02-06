"""Language-specific query patterns for tree-sitter parsers.

This module exports hard-coded patterns for specific languages such as Python, C, YAML, and JavaScript/TypeScript variants.
"""
from typing import Dict, Optional

from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

logger.debug("Loading language patterns", extra={
    'context': {
        'operation': 'initialization',
        'component': 'language_patterns'
    }
})

# JavaScript/TypeScript shared patterns
JS_TS_SHARED_PATTERNS = {
    "function": """
        [
          ; Regular function declaration
          (function_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @function.def
            
          ; Arrow function
          (arrow_function
            parameters: (formal_parameters) @function.params
            body: [
              (statement_block) @function.body
              (expression) @function.body
            ]) @function.def
            
          ; Method definition
          (method_definition
            name: (property_identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @function.def
            
          ; Function expression
          (function_expression
            name: (identifier)? @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @function.def
            
          ; Object method
          (method_definition
            name: (property_identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (statement_block) @function.body) @function.def

          ; Arrow function in variable declaration
          (variable_declarator
            name: (identifier) @function.name
            value: [
              (arrow_function
                parameters: (formal_parameters) @function.params
                body: [
                  (statement_block) @function.body
                  (expression) @function.body
                ]) @function.def
              (function_expression
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def
            ])

          ; Arrow function in object property
          (pair
            key: (property_identifier) @function.name
            value: [
              (arrow_function
                parameters: (formal_parameters) @function.params
                body: [
                  (statement_block) @function.body
                  (expression) @function.body
                ]) @function.def
              (function_expression
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def
            ])

          ; Arrow function in array
          (array
            [
              (arrow_function
                parameters: (formal_parameters) @function.params
                body: [
                  (statement_block) @function.body
                  (expression) @function.body
                ]) @function.def
              (function_expression
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def
            ])

          ; Arrow function in assignment
          (assignment_expression
            left: (_) @function.name
            right: [
              (arrow_function
                parameters: (formal_parameters) @function.params
                body: [
                  (statement_block) @function.body
                  (expression) @function.body
                ]) @function.def
              (function_expression
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def
            ])

          ; Arrow function in call expression arguments
          (call_expression
            arguments: (arguments
              [
                (arrow_function
                  parameters: (formal_parameters) @function.params
                  body: [
                    (statement_block) @function.body
                    (expression) @function.body
                  ]) @function.def
                (function_expression
                  parameters: (formal_parameters) @function.params
                  body: (statement_block) @function.body) @function.def
              ]))

          ; Arrow function in method chain
          (member_expression
            object: (call_expression
              function: (member_expression
                property: (property_identifier) @method.name)
              arguments: (arguments
                [
                  (arrow_function
                    parameters: (formal_parameters) @function.params
                    body: [
                      (statement_block) @function.body
                      (expression) @function.body
                    ]) @function.def
                  (function_expression
                    parameters: (formal_parameters) @function.params
                    body: (statement_block) @function.body) @function.def
                ])))

          ; Nested arrow function in method chain (e.g., map(x => x * 2))
          (call_expression
            function: (member_expression
              property: (property_identifier) @method.name)
            arguments: (arguments
              (arrow_function
                parameters: (formal_parameters) @function.params
                body: [
                  (statement_block) @function.body
                  (expression) @function.body
                ]) @function.def))

          ; Nested arrow function in method chain with multiple arguments
          (call_expression
            function: (member_expression
              property: (property_identifier) @method.name)
            arguments: (arguments
              [
                (arrow_function
                  parameters: (formal_parameters) @function.params
                  body: [
                    (statement_block) @function.body
                    (expression) @function.body
                  ]) @function.def
                (_)*
              ]))

          ; Arrow function in return statement
          (return_statement
            (arrow_function
              parameters: (formal_parameters) @function.params
              body: [
                (statement_block) @function.body
                (expression) @function.body
              ]) @function.def)
        ]
    """,
    "class": """
        (class_declaration
          name: (identifier) @class.name
          body: (class_body [
            (method_definition
              name: (property_identifier) @class.method.name
              parameters: (formal_parameters) @class.method.params
              body: (statement_block) @class.method.body)
            (public_field_definition
              name: (property_identifier) @class.field.name
              value: (_)? @class.field.value)
          ]*) @class.body
          extends: (extends_clause
            value: [
              (identifier) @class.extends
              (member_expression) @class.extends
            ])?) @class.def
    """,
    "import": """
        [
          ; ES6 imports
          (import_statement
            source: (string) @import.source
            clause: [
              ; Default import
              (import_clause
                (identifier) @import.default)
              ; Named imports
              (named_imports
                (import_specifier
                  name: (identifier) @import.name
                  alias: (identifier)? @import.alias)) 
            ]) @import
            
          ; Require
          (call_expression
            function: (identifier) @import.require
            (#eq? @import.require "require")
            arguments: (arguments (string) @import.source)) @import.require
            
          ; Dynamic import
          (call_expression
            function: (import) @import.dynamic
            arguments: (arguments (string) @import.source)) @import.dynamic
        ]
    """,
    "jsx_element": """
        [
          ; JSX/TSX Element
          (jsx_element
            opening_element: (jsx_opening_element
              name: (_) @jsx.tag.name
              attributes: (jsx_attributes
                (jsx_attribute
                  name: (jsx_attribute_name) @jsx.attr.name
                  value: (_)? @jsx.attr.value)*)?
            ) @jsx.open
            children: (_)* @jsx.children
            closing_element: (jsx_closing_element)? @jsx.close
          ) @jsx.element
          
          ; JSX/TSX Fragment
          (jsx_fragment
            children: (_)* @jsx.fragment.children
          ) @jsx.fragment
          
          ; JSX/TSX Expression
          (jsx_expression
            expression: (_) @jsx.expression.value
          ) @jsx.expression
        ]
    """
}

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
              ])) @class.def,
          (lambda
            parameters: (lambda_parameters)? @function.params
            body: (_) @function.body) @function.def
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

logger.debug("Python patterns loaded", extra={
    'context': {
        'operation': 'initialization',
        'component': 'language_patterns',
        'language': 'python',
        'pattern_count': len(PYTHON_PATTERNS)
    }
})

C_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_definition)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        (function_definition
          declarator: (function_declarator
            name: (identifier) @function.name
            parameters: (parameter_list) @function.params)
          body: (compound_statement) @function.body) @function.def
    """
}

logger.debug("C patterns loaded", extra={
    'context': {
        'operation': 'initialization',
        'component': 'language_patterns',
        'language': 'c',
        'pattern_count': len(C_PATTERNS)
    }
})

YAML_PATTERNS = {
    "mapping": """\
        (block_mapping_pair
          key: (_) @mapping.key
          value: (_) @mapping.value) @mapping
    """,
    "sequence": """\
        (block_sequence
          (block_sequence_item
            (_) @sequence.item)*) @sequence
    """,
    "anchor": """\
        (anchor
          name: (anchor_name) @anchor.name) @anchor
    """,
    "alias": """\
        (alias
          name: (alias_name) @alias.name) @alias
    """
}

logger.debug("YAML patterns loaded", extra={
    'context': {
        'operation': 'initialization',
        'component': 'language_patterns',
        'language': 'yaml',
        'pattern_count': len(YAML_PATTERNS)
    }
})

JS_VARIANT_PATTERNS = {
    "javascript": {
        # Basic pattern for function detection
        "function": """\
            [
              (function_declaration)
              (function_expression)
              (arrow_function)
              (method_definition)
            ] @function
        """,
        # Extended pattern for detailed function information
        "function_details": """\
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
        "class": """\
            [
              (class_declaration)
              (class_expression)
            ] @class
        """,
        "class_details": """\
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
        "module": """\
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
        "import": """\
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
            ]\
        """,
        "variable": """\
            (variable_declarator
               name: (identifier) @variable.name
               value: (_) @variable.value) @variable\
        """,
        "conditional": """\
            (if_statement
               condition: (parenthesized_expression)? @conditional.condition
               consequence: (block) @conditional.consequence
               (else_clause (block) @conditional.alternative)?) @conditional\
        """,
        "loop": """\
            [
              (for_statement
                (variable_declaration)? @loop.declaration
                body: (block) @loop.body),
              (while_statement
                condition: (parenthesized_expression)? @loop.condition
                body: (block) @loop.body)
            ] @loop\
        """,
        "lambda": """\
            (arrow_function
               parameters: (formal_parameters) @lambda.params
               body: [
                 (statement_block) @lambda.body
                 (expression) @lambda.body
               ]) @lambda\
        """,
        "assignment": """\
            (assignment_expression
               left: (identifier) @variable.name
               right: (_) @variable.value) @assignment\
        """
    },
    "typescript": {
        # Basic pattern for function detection
        "function": """\
            [
              (function_declaration)
              (function_expression)
              (arrow_function)
              (method_definition)
            ] @function
        """,
        # Extended pattern for detailed function information
        "function_details": """\
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
        # Type patterns
        "type_definition": """\
            [
              (type_alias_declaration
                name: (type_identifier) @type.name
                value: (_) @type.value) @type.def,
              (interface_declaration
                name: (type_identifier) @interface.name
                extends: (extends_type_clause
                  types: (type_list) @interface.extends)?
                body: (object_type) @interface.body) @interface.def,
              (enum_declaration
                name: (identifier) @enum.name
                body: (enum_body) @enum.body) @enum.def
            ]
        """,
        "type_annotation": """\
            [
              (type_annotation
                [
                  (type_identifier) @type.name
                  (union_type) @type.union
                  (intersection_type) @type.intersection
                  (generic_type) @type.generic
                ]) @type,
              (function_declaration
                return_type: (type_annotation) @function.return_type)
            ]
        """,
        "import": """\
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
            ]\
        """,
        "variable": """\
            (variable_declarator
               name: (identifier) @variable.name
               value: (_) @variable.value) @variable\
        """,
        "conditional": """\
            (if_statement
               condition: (parenthesized_expression)? @conditional.condition
               consequence: (block) @conditional.consequence
               (else_clause (block) @conditional.alternative)?) @conditional\
        """,
        "loop": """\
            [
              (for_statement
                (variable_declaration)? @loop.declaration
                body: (block) @loop.body),
              (while_statement
                condition: (parenthesized_expression)? @loop.condition
                body: (block) @loop.body)
            ] @loop\
        """,
        "lambda": """\
            (arrow_function
               parameters: (formal_parameters) @lambda.params
               body: [
                 (statement_block) @lambda.body
                 (expression) @lambda.body
               ]) @lambda\
        """,
        "assignment": """\
            (assignment_expression
               left: (identifier) @variable.name
               right: (_) @variable.value) @assignment\
        """
    }
}

TS_PATTERNS = {
    "interface": """\
        (interface_declaration
          name: (type_identifier) @interface.name
          extends_clause: (extends_type_clause
            types: (type_list
              (type_identifier) @interface.extends)*
          )? @interface.extends
          body: (object_type [
            (property_signature
              name: (property_identifier) @interface.property.name
              type: (type_annotation
                (type_identifier) @interface.property.type)?)
            (method_signature
              name: (property_identifier) @interface.method.name
              parameters: (formal_parameters) @interface.method.params
              type: (type_annotation)? @interface.method.return)?
          ]*) @interface.body) @interface.def\
    """,
    "type": """\
        [
          (type_alias_declaration
            name: (type_identifier) @type.name
            value: (_) @type.value) @type.def,
          (union_type
            types: (type_list) @type.union.types) @type.union,
          (intersection_type
            types: (type_list) @type.intersection.types) @type.intersection,
          (generic_type
            name: (type_identifier) @type.generic.name
            arguments: (type_arguments
              (type_identifier) @type.generic.arg)*) @type.generic
        ]\
    """,
    "enum": """\
        (enum_declaration
          name: (identifier) @enum.name
          body: (enum_body
            (enum_member
              name: (property_identifier) @enum.member.name
              value: (_)? @enum.member.value)*) @enum.body) @enum.def\
    """,
    "decorator": """\
        (decorator
          name: [
            (identifier) @decorator.name,
            (call_expression
              function: (identifier) @decorator.name
              arguments: (arguments) @decorator.args)
          ]) @decorator\
    """
};

TOML_PATTERNS = {
    "table": """\
        (table
          header: (table_header) @table.header
          entries: (pair
            key: (_) @table.key
            value: (_) @table.value)*) @table\
    """,
    "array": """\
        (array
          value: (_)* @array.value) @array\
    """,
    "inline_table": """\
        (inline_table
          (pair
            key: (_) @table.key
            value: (_) @table.value)*) @inline_table\
    """
}

DOCKERFILE_PATTERNS = {
    "instruction": """\
        (instruction
          cmd: (_) @instruction.cmd
          value: (_)* @instruction.value) @instruction\
    """,
    "from": """\
        (from_instruction
          image: (_) @from.image
          tag: (_)? @from.tag
          platform: (_)? @from.platform) @from\
    """,
    "run": """\
        (run_instruction
          command: (_) @run.command) @run\
    """
};

MARKDOWN_PATTERNS = {
    "heading": """\
        (atx_heading
          marker: (_) @heading.marker
          content: (_) @heading.content) @heading\
    """,
    "list": """\
        (list
          item: (list_item
            content: (_) @list.item.content)*) @list\
    """,
    "link": """\
        [
          (link
            text: (_) @link.text
            url: (_) @link.url) @link,
          (image
            text: (_) @image.text
            url: (_) @image.url) @image
        ]\
    """,
    "code_block": """\
        [
          (fenced_code_block
            language: (_)? @code.language
            content: (_) @code.content) @code.block,
          (indented_code_block) @code.indented
        ]\
    """,
    "blockquote": """\
        (block_quote
          content: (_) @quote.content) @quote\
    """
}

JAVA_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (method_declaration)
          (constructor_declaration)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (method_declaration
            modifiers: (modifiers)? @function.modifiers
            type: (_) @function.return_type
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            throws: (throws)? @function.throws
            body: (block) @function.body
            [
              (comment)* @function.javadoc
            ]?) @function.def,
          (constructor_declaration
            modifiers: (modifiers)? @function.modifiers
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            throws: (throws)? @function.throws
            body: (block) @function.body) @function.def
        ]
    """,
    # Class patterns
    "class": """\
        [
          (class_declaration)
          (interface_declaration)
          (enum_declaration)
        ] @class
    """,
    "class_details": """\
        [
          (class_declaration
            modifiers: (modifiers)? @class.modifiers
            name: (identifier) @class.name
            type_parameters: (type_parameters)? @class.type_params
            superclass: (superclass)? @class.extends
            interfaces: (super_interfaces)? @class.implements
            body: (class_body
              [
                (field_declaration)* @class.fields
                (method_declaration)* @class.methods
                (constructor_declaration)* @class.constructors
                (class_declaration)* @class.inner_classes
              ]
              [
                (comment)* @class.javadoc
              ]?)) @class.def,
          (interface_declaration
            modifiers: (modifiers)? @interface.modifiers
            name: (identifier) @interface.name
            type_parameters: (type_parameters)? @interface.type_params
            interfaces: (extends_interfaces)? @interface.extends
            body: (interface_body
              [
                (constant_declaration)* @interface.constants
                (method_declaration)* @interface.methods
              ])) @interface.def,
          (enum_declaration
            modifiers: (modifiers)? @enum.modifiers
            name: (identifier) @enum.name
            interfaces: (super_interfaces)? @enum.implements
            body: (enum_body
              [
                (enum_constant)* @enum.constants
                (field_declaration)* @enum.fields
                (method_declaration)* @enum.methods
              ])) @enum.def
        ]
    """,
    # Package and module patterns
    "package": """\
        [
          (package_declaration
            name: (identifier) @package.name) @package,
          (module_declaration
            name: (identifier) @module.name
            body: (module_body
              [
                (requires_module_directive)* @module.requires
                (exports_module_directive)* @module.exports
                (opens_module_directive)* @module.opens
              ])) @module
        ]
    """,
    # Type patterns
    "type": """\
        [
          (type_identifier) @type.name,
          (generic_type
            type: (type_identifier) @type.generic.base
            type_arguments: (type_arguments
              (_)* @type.generic.args)) @type.generic,
          (wildcard
            bound: (type_bound)? @type.wildcard.bound) @type.wildcard
        ]
    """,
    # Documentation patterns
    "documentation": """\
        [
          (comment) @comment
          (line_comment) @comment.line
          (block_comment) @comment.block
          (javadoc_comment) @comment.javadoc
        ]
    """,
    "import": """\
        (import_declaration
          name: (qualified_identifier) @import.name) @import
    """,
    "variable": """\
        (local_variable_declaration
           (variable_declarator
             name: (identifier) @variable.name)) @variable
    """,
    "conditional": """\
        (if_statement
          condition: (parenthesized_expression)? @conditional.condition
          consequence: (block) @conditional.consequence
          (else_clause (block) @conditional.alternative)?) @conditional
    """,
    "loop": """\
        [
          (for_statement
            (for_init)? @loop.init
            condition: (parenthesized_expression)? @loop.condition
            (for_update)? @loop.update
            body: (block) @loop.body),
          (while_statement
            condition: (parenthesized_expression)? @loop.condition
            body: (block) @loop.body)
        ] @loop
    """,
    "lambda": """\
        (lambda_expression
            parameters: (inferred_parameters)? @lambda.params
            body: (_) @lambda.body) @lambda
    """,
    "spring_annotations": """\
        [
            (annotation
                name: (identifier) @spring.annotation.name
                (#match? @spring.annotation.name "^(Controller|Service|Repository|Component|Autowired|RequestMapping|GetMapping|PostMapping)$")
                arguments: (annotation_argument_list)? @spring.annotation.args) @spring.annotation,
            (class_declaration
                (modifiers
                    (annotation
                        name: (identifier) @spring.class.annotation
                        (#match? @spring.class.annotation "^(Controller|Service|Repository|Component)$")
                        arguments: (annotation_argument_list)? @spring.class.args))) @spring.class
        ]
    """
}

GO_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_declaration)
          (method_declaration)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
        (function_declaration
           name: (identifier) @function.name
            parameters: (parameter_list
              (parameter_declaration
                name: (identifier) @function.param.name
                type: (_) @function.param.type)*) @function.params
            result: (parameter_list)? @function.return_type
            body: (block) @function.body) @function.def,
          (method_declaration
            receiver: (parameter_list
              (parameter_declaration
                name: (identifier)? @function.receiver.name
                type: (_) @function.receiver.type)) @function.receiver
            name: (identifier) @function.name
            parameters: (parameter_list
              (parameter_declaration
                name: (identifier) @function.param.name
                type: (_) @function.param.type)*) @function.params
            result: (parameter_list)? @function.return_type
            body: (block) @function.body) @function.def
        ]
    """,
    # Type patterns
    "type": """\
        [
          (type_declaration
            (type_spec
              name: (type_identifier) @type.name
              type: (_) @type.value)) @type.def,
          (type_identifier) @type.ref
        ]
    """,
    # Interface patterns
    "interface": """\
        (interface_type
          (method_spec
            name: (identifier) @interface.method.name
            parameters: (parameter_list) @interface.method.params
            result: (parameter_list)? @interface.method.return_type)*) @interface
    """,
    # Struct patterns
    "struct": """\
        (struct_type
          (field_declaration_list
            (field_declaration
              name: (field_identifier) @struct.field.name
              type: (_) @struct.field.type
              tag: (raw_string_literal)? @struct.field.tag)*)) @struct
    """,
    # Package patterns
    "package": """\
        [
          (package_clause
            (package_identifier) @package.name) @package,
        (import_declaration
            (import_spec_list
              (import_spec
                name: (identifier)? @import.alias
                path: (interpreted_string_literal) @import.path)*)) @import
        ]
    """,
    # Variable declaration patterns
    "variable": """\
        [
          (var_declaration
            (var_spec
              name: (identifier) @variable.name
              type: (_)? @variable.type
              value: (_)? @variable.value)) @variable.def,
        (short_var_declaration
            left: (expression_list
              (identifier) @variable.name)
            right: (expression_list
              (_) @variable.value)) @variable.short_def
        ]
    """,
    # Control flow patterns
    "control_flow": """\
        [
        (if_statement
            condition: (_) @if.condition
            body: (block) @if.body
            else: (block)? @if.else) @if,
          (for_statement
            clause: (_)? @for.clause
            body: (block) @for.body) @for,
          (range_statement
            left: (_)? @range.vars
            right: (_) @range.expr
            body: (block) @range.body) @range
        ]
    """,
    # Channel operation patterns
    "channel": """\
        [
          (channel_type) @channel.type,
          (send_statement
            channel: (_) @channel.name
            value: (_) @channel.value) @channel.send,
          (receive_statement
            left: (_) @channel.receiver
            right: (_) @channel.source) @channel.receive
        ]
    """,
    # Error handling patterns
    "error_handling": """\
        [
          (defer_statement
            (_) @defer.expr) @defer,
          (go_statement
            (_) @go.expr) @go,
          (return_statement
            (_)* @return.values) @return
        ]
    """,
    "build_tags": """\
        (comment
            text: (comment) @build.tag.text
            (#match? @build.tag.text "^//\\s*\\+build.*$")) @build.tag
    """,
    "generate": """\
        (comment
            text: (comment) @generate.text
            (#match? @generate.text "^//go:generate.*$")) @generate
    """
}

RUST_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_item)
          (closure_expression)
          (async_block_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
        (function_item
           name: (identifier) @function.name
            parameters: (parameters
              (parameter
                pattern: (_) @function.param.name
                type: (_) @function.param.type)*) @function.params
            return_type: (_)? @function.return_type
            body: (block) @function.body
            [
              (attribute_item)* @function.attributes
              (comment)* @function.doc
            ]?) @function.def,
          (closure_expression
            parameters: (parameters)? @function.params
            return_type: (_)? @function.return_type
            body: (block) @function.body) @function.closure,
          (async_block_expression
            body: (block) @function.async.body) @function.async
        ]
    """,
    # Trait patterns
    "trait": """\
        (trait_item
          name: (identifier) @trait.name
          type_parameters: (type_parameters)? @trait.type_params
          bounds: (trait_bounds)? @trait.bounds
          body: (declaration_list
            [
              (function_item)* @trait.methods
              (type_item)* @trait.types
              (const_item)* @trait.constants
              (macro_invocation)* @trait.macros
            ])) @trait.def
    """,
    # Implementation patterns
    "impl": """\
        [
          (impl_item
            type: (type_identifier) @impl.type
            trait: (type_identifier)? @impl.trait
            body: (declaration_list
              [
                (function_item)* @impl.methods
                (type_item)* @impl.types
                (const_item)* @impl.constants
                (macro_invocation)* @impl.macros
              ])) @impl.def,
          (impl_item
            type: (generic_type) @impl.generic.type
            trait: (generic_type)? @impl.generic.trait
            body: (declaration_list)) @impl.generic
        ]
    """,
    # Macro patterns
    "macro": """\
        [
          (macro_definition
            name: (identifier) @macro.name
            parameters: (macro_parameters)? @macro.params
            body: (macro_body) @macro.body) @macro.def,
          (macro_invocation
            macro: (identifier) @macro.call.name
            arguments: (token_tree) @macro.call.args) @macro.call
        ]
    """,
    # Lifetime patterns
    "lifetime": """\
        [
          (lifetime
            (identifier) @lifetime.name) @lifetime,
          (lifetime_constraint
            lifetime: (lifetime) @lifetime.constrained
            bounds: (lifetime_bounds
              (lifetime)* @lifetime.bound)) @lifetime.constraint
        ]
    """,
    # Type patterns
    "type": """\
        [
          (type_item
            name: (type_identifier) @type.name
            type_parameters: (type_parameters)? @type.params
            body: (_) @type.body) @type.def,
          (type_identifier) @type.ref,
          (generic_type
            type: (type_identifier) @type.generic.base
            arguments: (type_arguments
              (_)* @type.generic.args)) @type.generic
        ]
    """,
    # Module patterns
    "module": """\
        [
          (mod_item
            name: (identifier) @module.name
            body: (declaration_list)? @module.body) @module,
          (extern_crate
            name: (identifier) @crate.name
            alias: (identifier)? @crate.alias) @crate
        ]
    """,
    # Attribute patterns
    "attribute": """\
        [
          (attribute_item
            path: (identifier) @attribute.name
            arguments: (token_tree)? @attribute.args) @attribute,
          (inner_attribute_item
            path: (identifier) @attribute.inner.name
            arguments: (token_tree)? @attribute.inner.args) @attribute.inner
        ]
    """,
    # Documentation patterns
    "documentation": """\
        [
          (line_comment) @doc.line,
          (block_comment) @doc.block,
          (attribute_item
            path: (identifier) @doc.attr.name
            (#match? @doc.attr.name "^doc$")
            arguments: (token_tree) @doc.attr.content) @doc.attr
        ]
    """
}

CPP_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_definition)
          (method_definition)
          (lambda_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
        (function_definition
            type: (primitive_type)? @function.return_type
           declarator: (function_declarator
              declarator: (identifier) @function.name
              parameters: (parameter_list
                (parameter_declaration
                  type: (_) @function.param.type
                  declarator: (identifier) @function.param.name)*) @function.params)
            body: (compound_statement) @function.body) @function.def,
          (method_definition
            type: (_)? @function.return_type
            declarator: (function_declarator
              declarator: (identifier) @function.name
              parameters: (parameter_list
                (parameter_declaration
                  type: (_) @function.param.type
                  declarator: (identifier) @function.param.name)*) @function.params)
            body: (compound_statement) @function.body) @function.def,
          (lambda_expression
            captures: (lambda_capture_specifier)? @function.captures
            parameters: (parameter_list)? @function.params
            body: [
              (compound_statement) @function.body
              (expression_statement) @function.body
            ]) @function.lambda
        ]
    """,
    # Class patterns
    "class": """\
        [
          (class_specifier
            name: (type_identifier) @class.name
            bases: (base_class_clause
              (base_class
                name: (type_identifier) @class.base
                access_specifier: (_)? @class.base.access)*)?
            body: (field_declaration_list
              [
                (access_specifier) @class.access
                (field_declaration
                  type: (_) @class.field.type
                  declarator: (field_identifier) @class.field.name)*
                (function_definition)* @class.methods
              ])) @class.def,
          (struct_specifier
            name: (type_identifier) @struct.name
            body: (field_declaration_list)) @struct.def
        ]
    """,
    # Template patterns
    "template": """\
        [
          (template_declaration
            parameters: (template_parameter_list
              [
                (type_parameter_declaration
                  name: (type_identifier) @template.param.name)
                (parameter_declaration
                  type: (_) @template.param.type
                  declarator: (identifier) @template.param.name)
                )
              ]*) @template.params
            declaration: (_) @template.body) @template.def,
          (template_instantiation
            name: (identifier) @template.inst.name
            arguments: (template_argument_list
              (_)* @template.inst.args)) @template.inst
        ]
    """,
    # Namespace patterns
    "namespace": """\
        [
          (namespace_definition
            name: (identifier) @namespace.name
            body: (declaration_list) @namespace.body) @namespace.def,
          (using_declaration
            name: (qualified_identifier) @using.name) @using,
          (using_directive
            name: (qualified_identifier) @using.namespace) @using.directive
        ]
    """,
    # Type patterns
    "type": """\
        [
          (type_identifier) @type.name,
          (primitive_type) @type.primitive,
          (sized_type_specifier) @type.sized,
          (type_qualifier) @type.qualifier,
          (enum_specifier
            name: (type_identifier) @enum.name
            body: (enumerator_list
              (enumerator
                name: (identifier) @enum.value.name
                value: (_)? @enum.value.init)*)) @enum.def
        ]
    """,
    # Operator patterns
    "operator": """\
        [
          (operator_name) @operator.name,
          (operator_cast
            type: (_) @operator.cast.type) @operator.cast,
          (operator_assignment) @operator.assignment,
          (operator_binary) @operator.binary,
          (operator_unary) @operator.unary
        ]
    """,
    # Exception handling patterns
    "exception": """\
        [
          (try_statement
            body: (compound_statement) @try.body
            (catch_clause
              parameters: (parameter_list) @catch.params
              body: (compound_statement) @catch.body)*
            (finally_clause
              body: (compound_statement))? @finally.body) @try,
          (throw_statement
            value: (_) @throw.value) @throw
        ]
    """,
    # Memory management patterns
    "memory": """\
        [
          (new_expression
            type: (_) @new.type
            arguments: (argument_list)? @new.args) @new,
          (delete_expression
            value: (_) @delete.value) @delete,
          (pointer_expression
            operator: (_) @pointer.op
            argument: (_) @pointer.arg) @pointer
        ]
    """,
    # Preprocessor patterns
    "preprocessor": """\
        [
          (preproc_include
            path: (_) @include.path) @include,
          (preproc_def
            name: (identifier) @define.name
            value: (_)? @define.value) @define,
          (preproc_ifdef
            name: (identifier) @ifdef.name) @ifdef,
          (preproc_function_def
            name: (identifier) @macro.name
            parameters: (preproc_params)? @macro.params) @macro
        ]
    """,
    "modern_features": """\
        [
            (concept_definition
                name: (identifier) @concept.name
                parameters: (template_parameter_list)? @concept.params
                body: (_) @concept.body) @concept,
            (requires_clause
                requirements: (_) @requires.constraints) @requires,
            (range_based_for_statement
                declarator: (_) @range.var
                range: (_) @range.expr
                body: (_) @range.body) @range,
            (fold_expression
                pack: (_) @fold.pack
                operator: (_) @fold.op) @fold,
            (structured_binding_declaration
                bindings: (identifier)* @binding.names
                value: (_) @binding.value) @binding
        ]
    """
}

RUBY_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (method)
          (singleton_method)
          (block)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (method
            name: (identifier) @function.name
            parameters: (method_parameters
              [
                (identifier) @function.param.name
                (optional_parameter
                  name: (identifier) @function.param.name
                  value: (_) @function.param.default)
                (keyword_parameter
                  name: (identifier) @function.param.name
                  value: (_)? @function.param.default)
                (rest_parameter
                  name: (identifier) @function.param.rest)
                (block_parameter
                  name: (identifier) @function.param.block)
              ]*) @function.params
            [
              (body_statement) @function.body
              (comment)* @function.doc
            ]) @function.def,
          (singleton_method
            object: (_) @function.singleton
            name: (identifier) @function.name
            parameters: (method_parameters)? @function.params
            body: (body_statement) @function.body) @function.def,
          (block
            parameters: (block_parameters)? @block.params
            body: (body_statement) @block.body) @block.do
        ]
    """,
    # Class patterns
    "class": """\
        [
          (class
            name: (constant) @class.name
            superclass: (superclass
              value: (constant) @class.superclass)?
            body: (body_statement
              [
                (comment)* @class.doc
                (method)* @class.methods
                (singleton_class
                  value: (self) @class.singleton
                  body: (body_statement))* @class.singleton_methods
              ])) @class.def,
          (singleton_class
            value: (_) @class.singleton.value
            body: (body_statement) @class.singleton.body) @class.singleton
        ]
    """,
    # Module patterns
    "module": """\
        (module
          name: (constant) @module.name
          body: (body_statement
            [
              (comment)* @module.doc
              (method)* @module.methods
              (module_function
                (identifier)* @module.function)*
              ])) @module.def
    """,
    # Metaprogramming patterns
    "metaprogramming": """\
        [
        (call
            receiver: (_)?
            method: [
              (identifier) @meta.method
              (#match? @meta.method "^(define_method|alias_method|attr_accessor|attr_reader|attr_writer|include|extend|prepend)$")
            ]
            arguments: (argument_list
              (_)* @meta.args)) @meta.call,
          (class_variable) @meta.class_var,
          (instance_variable) @meta.instance_var
        ]
    """,
    # Block patterns
    "block": """\
        [
          (do_block
            parameters: (block_parameters)? @block.params
            body: (body_statement) @block.body) @block.do,
          (block
            parameters: (block_parameters)? @block.params
            body: (body_statement) @block.body) @block.brace
        ]
    """,
    # Control flow patterns
    "control_flow": """\
        [
          (if
            condition: (_) @if.condition
            consequence: (_) @if.then
            alternative: (_)? @if.else) @if,
          (unless
            condition: (_) @unless.condition
            consequence: (_) @unless.then
            alternative: (_)? @unless.else) @unless,
          (while
            condition: (_) @while.condition
            body: (_) @while.body) @while,
          (until
            condition: (_) @until.condition
            body: (_) @until.body) @until,
          (for
            pattern: (_) @for.pattern
            collection: (_) @for.collection
            body: (_) @for.body) @for,
          (case
            value: (_)? @case.value
            (when
              pattern: (_) @when.pattern
              body: (_) @when.body)*
            else: (_)? @case.else) @case
        ]
    """,
    # Exception handling patterns
    "exception": """\
        [
          (begin
            body: (_) @begin.body
            (rescue
              exception: (_)? @rescue.type
              variable: (_)? @rescue.var
              body: (_) @rescue.body)*
            (else
              body: (_) @rescue.else)?
            (ensure
              body: (_) @rescue.ensure)?) @begin,
          (rescue_modifier
            body: (_) @rescue_mod.body
            handler: (_) @rescue_mod.handler) @rescue_mod
        ]
    """,
    # String patterns
    "string": """\
        [
          (string
            (string_content) @string.content) @string,
          (heredoc_beginning) @heredoc.start
          (heredoc_body
            (string_content) @heredoc.content) @heredoc,
          (interpolation
            (_) @string.interpolation) @interpolation
        ]
    """,
    # Symbol patterns
    "symbol": """\
        [
          (simple_symbol) @symbol,
          (hash_key_symbol) @symbol.key,
          (symbol_array) @symbol.array
        ]
    """,
    "rails_patterns": """\
        [
            (call
                method: (identifier) @rails.method
                (#match? @rails.method "^(belongs_to|has_many|has_one|validates|scope|before_action|after_action)$")
                arguments: (argument_list)? @rails.args) @rails.call,
            (class
                (constant) @model.name
                (superclass
                    (constant) @model.parent
                    (#match? @model.parent "^(ApplicationRecord|ActiveRecord::Base)$"))) @model
        ]
    """,
    "meta_programming": """\
        [
            (call
                method: (identifier) @meta.method
                (#match? @meta.method "^(class_eval|instance_eval|define_method|method_missing|respond_to_missing\\?)$")
                arguments: (argument_list)? @meta.args) @meta.call,
            (singleton_class
                value: (_) @meta.target
                body: (body_statement) @meta.body) @meta.singleton
        ]
    """
}

PHP_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_definition)
          (method_declaration)
          (arrow_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
        (function_definition
            name: (name) @function.name
            parameters: (formal_parameters
              (parameter_declaration
                type: (_)? @function.param.type
                name: (variable_name) @function.param.name
                default_value: (_)? @function.param.default)*) @function.params
            return_type: (_)? @function.return_type
            body: (compound_statement) @function.body
            [
              (text) @function.doc
            ]?) @function.def,
          (method_declaration
            modifiers: (member_modifier)* @function.modifiers
            name: (name) @function.name
            parameters: (formal_parameters
              (parameter_declaration
                type: (_)? @function.param.type
                name: (variable_name) @function.param.name
                default_value: (_)? @function.param.default)*) @function.params
            return_type: (_)? @function.return_type
            body: (compound_statement) @function.body
            [
              (text) @function.doc
            ]?) @function.def,
          (arrow_function
            parameters: (formal_parameters
              (parameter_declaration
                type: (_)? @function.param.type
                name: (variable_name) @function.param.name)*) @function.params
            return_type: (_)? @function.return_type
            body: (_) @function.body) @function.arrow
        ]
    """,
    # Class patterns
    "class": """\
        [
          (class_declaration
            modifiers: (member_modifier)* @class.modifiers
            name: (name) @class.name
            extends: (base_clause
              (name) @class.extends)?
            implements: (class_interface_clause
              (name)* @class.implements)?
            body: (declaration_list
              [
                (field_declaration)* @class.fields
                (property_declaration)* @class.properties
                (method_declaration)* @class.methods
                (constructor_declaration)* @class.constructors
              ]
              [
                (text) @class.doc
              ]?)) @class.def
        ]
    """,
    # Interface patterns
    "interface": """\
        (interface_declaration
          name: (name) @interface.name
          extends: (base_clause
            (name)* @interface.extends)?
          body: (declaration_list
            [
              (property_declaration)* @interface.properties
              (method_declaration)* @interface.methods
            ]
            [
              (text) @interface.doc
            ]?)) @interface.def
    """,
    # Trait patterns
    "trait": """\
        (trait_declaration
          name: (name) @trait.name
          body: (declaration_list
            [
              (method_declaration)* @trait.methods
              (property_declaration)* @trait.properties
            ]
            [
              (text) @trait.doc
            ]?)) @trait.def
    """,
    # Namespace patterns
    "namespace": """\
        [
          (namespace_definition
            name: (identifier) @namespace.name
            body: (compound_statement)? @namespace.body) @namespace.def,
          (using_declaration
            name: (qualified_name) @use.name) @use
        ]
    """,
    # Type patterns
    "type": """\
        [
          (primitive_type) @type.primitive,
          (cast_type) @type.cast,
          (named_type) @type.named,
          (nullable_type) @type.nullable,
          (union_type) @type.union,
          (intersection_type) @type.intersection
        ]
    """,
    # Control flow patterns
    "control_flow": """\
        [
          (if_statement
            condition: (parenthesized_expression) @if.condition
            body: (_) @if.body
            else: (_)? @if.else) @if,
          (foreach_statement
            collection: (_) @foreach.collection
            value: (_) @foreach.value
            key: (_)? @foreach.key
            body: (_) @foreach.body) @foreach,
          (while_statement
            condition: (parenthesized_expression) @while.condition
            body: (_) @while.body) @while,
          (do_statement
            body: (_) @do.body
            condition: (parenthesized_expression) @do.condition) @do,
          (for_statement
            initializations: (_)? @for.init
            condition: (_)? @for.condition
            increments: (_)? @for.increment
            body: (_) @for.body) @for,
          (switch_statement
            condition: (parenthesized_expression) @switch.condition
            body: (switch_block
              (case_statement
                value: (_) @case.value
                body: (_)? @case.body)*
              (default_statement
                body: (_)? @default.body)?)) @switch
        ]
    """,
    # Exception handling patterns
    "exception": """\
        [
          (try_statement
            body: (compound_statement) @try.body
            (catch_clause
              type: (qualified_name) @catch.type
              name: (variable_name) @catch.name
              body: (compound_statement) @catch.body)*
            (finally_clause
              body: (compound_statement))? @finally.body) @try,
          (throw_expression
            value: (_) @throw.value) @throw
        ]
    """,
    # Variable patterns
    "variable": """\
        [
          (variable_name) @variable.name,
          (property_element
            name: (variable_name) @property.name) @property,
          (array_creation_expression
            elements: (array_element_initializer
              key: (_)? @array.key
              value: (_) @array.value)*) @array
        ]
    """,
    # String patterns
    "string": """\
        [
          (string) @string,
          (encapsed_string
            (string_value) @string.content
            (variable_name)* @string.var) @string.complex,
          (heredoc
            (string_value) @heredoc.content) @heredoc
        ]
    """,
    "attributes": """\
        [
            (attribute_list
                (attribute
                    name: (name) @attribute.name
                    arguments: (arguments)? @attribute.args)) @attribute,
            (attribute_group
                (attribute
                    name: (name) @attribute.group.name
                    arguments: (arguments)? @attribute.group.args)) @attribute.group
        ]
    """,
    "framework_patterns": """\
        [
            (attribute_list
                (attribute
                    name: (name) @framework.attribute
                    (#match? @framework.attribute "^(Route|Controller|Entity|Column)$")
                    arguments: (arguments)? @framework.args)) @framework,
            (class_declaration
                (name) @controller.name
                (base_clause
                    (name) @controller.base
                    (#match? @controller.base "^.*Controller$"))) @controller
        ]
    """
}

SWIFT_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_declaration)
          (closure_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (function_declaration
            name: (identifier) @function.name
            parameters: (parameter_clause) @function.params
            body: (code_block) @function.body) @function.def,
          (closure_expression
            parameters: (parameter_clause)? @function.params
            body: (code_block) @function.body) @function.def
        ]
    """
};

KOTLIN_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_declaration)
          (lambda_literal)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
        (function_declaration
           name: (simple_identifier) @function.name
            parameters: (parameter_list) @function.params
            body: (function_body) @function.body) @function.def,
          (lambda_literal
            parameters: (parameter_list)? @function.params
            body: (statements) @function.body) @function.def
        ]
    """,
    "coroutines": """\
        [
            (function_declaration
                modifiers: (modifiers
                    (annotation
                        (#match? @annotation.name "^Suspend$"))) @coroutine.modifiers
                name: (simple_identifier) @coroutine.name
                body: (function_body) @coroutine.body) @coroutine,
            (call_expression
                function: [
                    (simple_identifier) @coroutine.launch
                    (#match? @coroutine.launch "^(launch|async|withContext)$")
                ]
                lambda: (lambda_literal) @coroutine.block) @coroutine.call
        ]
    """,
    "dsl": """\
        [
            (class_declaration
                modifiers: (modifiers
                    (annotation
                        (#match? @annotation.name "^DslMarker$"))) @dsl.marker
                name: (simple_identifier) @dsl.name
                body: (class_body) @dsl.body) @dsl.class,
            (function_declaration
                modifiers: (modifiers
                    (annotation
                        (#match? @annotation.name "^BuilderDsl$"))) @dsl.builder.modifiers
                name: (simple_identifier) @dsl.builder.name
                body: (function_body) @dsl.builder.body) @dsl.builder
        ]
    """,
    "spring": """\
        [
            (class_declaration
                modifiers: (modifiers
                    (annotation
                        (#match? @annotation.name "^(Controller|Service|Repository|Component)$"))) @spring.component.type
                name: (simple_identifier) @spring.component.name) @spring.component,
            (function_declaration
                modifiers: (modifiers
                    (annotation
                        (#match? @annotation.name "^(GetMapping|PostMapping|PutMapping|DeleteMapping)$"))) @spring.endpoint.type
                name: (simple_identifier) @spring.endpoint.name) @spring.endpoint
        ]
    """
}

HTML_PATTERNS = {
    "element": """\
        [
          ; Regular elements
          (element
            (start_tag
              (tag_name) @element.name
              (attribute
                (attribute_name) @element.attr.name
                [
                  (attribute_value) @element.attr.value
                  (quoted_attribute_value
                    (attribute_value) @element.attr.value)
                  ])* @element.attrs)
            (_)* @element.children
            (end_tag)?) @element.def
          
          ; Self-closing elements
          (element
            (self_closing_tag
              (tag_name) @element.name
              (attribute
                (attribute_name) @element.attr.name
                [
                  (attribute_value) @element.attr.value
                  (quoted_attribute_value
                    (attribute_value) @element.attr.value)
                  ])* @element.attrs)) @element.self_closing
        ] @element.any
    """,
    "document": """\
        (document
          (doctype)? @document.doctype
          (_)* @document.content) @document
    """,
    "comment": """\
        (comment) @comment
    """,
    "attribute": """\
        (attribute
          name: (attribute_name) @attribute.name
          value: (attribute_value)? @attribute.value) @attribute
    """
}

BASH_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_definition)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
          (function_definition
            name: (word) @function.name
          body: [
            (compound_command) @function.body
            (command) @function.body
          ]) @function.def
    """
}

DART_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_signature)
          (method_signature)
          (constructor_signature)
          (function_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (function_signature
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def,
          (method_signature
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def,
          (constructor_signature
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def,
          (function_expression
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def
        ]
    """,
    "import": """\
        [
          (import_directive
            uri: (string) @import.source) @import
        ]
    """
}

ELIXIR_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (call target: (identifier) (#match? @identifier "^(def|defp|defmacro)$"))
          (anonymous_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (call
            target: (identifier) @def.keyword
            (#match? @def.keyword "^(def|defp|defmacro)$")
            (_) @function.name
            (_)* @function.body) @function.def,
          (anonymous_function
            parameters: (vector) @function.params
            body: (expression) @function.body) @function.def
        ]
    """,
    "module": """\
        (module
          name: (alias) @module.name
          body: (do_block) @module.body) @module.def
    """
}

ADA_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (subprogram_body)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
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
    "function": """\
        [
          (function_declaration)
          (lambda_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
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
    "import": """\
        (import_declaration 
            module: (module_name) @import.name) @import
    """
}

PERL_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (subroutine_definition)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (subroutine_definition
             name: (identifier) @function.name
            body: (block) @function.body) @function.def
        ]
    """
}

OBJECTIVEC_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (method_declaration)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
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
    "function": """\
        [
          (function_declaration)
          (local_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
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

SCALA_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (function_definition)
          (method_definition)
          (anonymous_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (function_definition
            modifiers: (modifiers)? @function.modifiers
             name: (identifier) @function.name
            type_parameters: (type_parameter_list)? @function.type_params
            parameters: (parameter_list
              (parameter
                modifiers: (modifiers)? @function.param.modifiers
                name: (identifier) @function.param.name
                type: (_) @function.param.type
                default: (_)? @function.param.default)*) @function.params
            return_type: (_)? @function.return_type
            body: (block) @function.body) @function.def,
          (method_definition
            modifiers: (modifiers)? @function.modifiers
             name: (identifier) @function.name
            type_parameters: (type_parameter_list)? @function.type_params
            parameters: (parameter_list) @function.params
            return_type: (_)? @function.return_type
            body: (block) @function.body) @function.def,
          (anonymous_function
             parameters: (parameter_list)? @function.params
            body: (_) @function.body) @function.lambda
        ]
    """,
    # Class patterns
    "class": """\
        [
          (class_definition)
          (trait_definition)
          (object_definition)
          (case_class_definition)
        ] @class
    """,
    "class_details": """\
        [
          (class_definition
            modifiers: (modifiers)? @class.modifiers
            name: (identifier) @class.name
            type_parameters: (type_parameter_list)? @class.type_params
            constructor_parameters: (constructor_parameter_list
              (parameter
                modifiers: (modifiers)? @class.param.modifiers
                name: (identifier) @class.param.name
                type: (_) @class.param.type)*) @class.params
            extends_clause: (extends_clause)? @class.extends
            with_clause: (with_clause)? @class.with
            body: (template_body
              [
                (function_definition)* @class.methods
                (value_definition)* @class.values
                (variable_definition)* @class.vars
                (type_definition)* @class.types
              ]) @class.body) @class.def,
          (trait_definition
            modifiers: (modifiers)? @trait.modifiers
            name: (identifier) @trait.name
            type_parameters: (type_parameter_list)? @trait.type_params
            extends_clause: (extends_clause)? @trait.extends
            with_clause: (with_clause)? @trait.with
            body: (template_body) @trait.body) @trait.def,
          (object_definition
            modifiers: (modifiers)? @object.modifiers
            name: (identifier) @object.name
            extends_clause: (extends_clause)? @object.extends
            with_clause: (with_clause)? @object.with
            body: (template_body) @object.body) @object.def,
          (case_class_definition
            modifiers: (modifiers)? @case_class.modifiers
            name: (identifier) @case_class.name
            type_parameters: (type_parameter_list)? @case_class.type_params
            parameters: (constructor_parameter_list) @case_class.params
            extends_clause: (extends_clause)? @case_class.extends
            with_clause: (with_clause)? @case_class.with
            body: (template_body)? @case_class.body) @case_class.def
        ]
    """,
    # Package patterns
    "package": """\
        [
          (package_clause
            name: (qualified_name) @package.name) @package,
          (package_object
            name: (identifier) @package.object.name
            body: (template_body) @package.object.body) @package.object
        ]
    """,
    # Import patterns
    "import": """\
        [
          (import_declaration
            importers: (import_selectors
              (import_selector
                name: (identifier) @import.name
                rename: (identifier)? @import.rename)*) @import.selectors) @import,
          (import_expression
            qualifier: (qualified_name) @import.qualifier
            selectors: (import_selectors)? @import.selectors) @import.expr
        ]
    """,
    # Type patterns
    "type": """\
        [
          (type_definition
            modifiers: (modifiers)? @type.modifiers
            name: (identifier) @type.name
            type_parameters: (type_parameter_list)? @type.params
            body: (_) @type.body) @type.def,
          (type_projection
            type: (_) @type.proj.type) @type.projection,
          (existential_type
            type: (_) @type.exist.type
            declarations: (existential_declarations) @type.exist.decls) @type.existential,
          (compound_type
            types: (_)* @type.compound.types) @type.compound
        ]
    """,
    # Pattern matching patterns
    "pattern_matching": """\
        [
          (match_expression
            expression: (_) @match.expr
            cases: (case_clause
              pattern: (_) @case.pattern
              guard: (_)? @case.guard
              body: (_) @case.body)*) @match,
          (pattern_definition
            pattern: (_) @pattern.pattern
            type: (_)? @pattern.type
            body: (_) @pattern.body) @pattern
        ]
    """,
    # For comprehension patterns
    "for_comprehension": """\
        [
          (for_expression
            enumerators: (enumerators
              (generator
                pattern: (_) @for.pattern
                expression: (_) @for.expr)*
              (guard)* @for.guard) @for.enums
            body: (_) @for.body) @for
        ]
    """,
    # Implicit patterns
    "implicit": """\
        [
          (function_definition
            modifiers: (modifiers
              (modifier) @implicit.modifier
              (#eq? @implicit.modifier "implicit")) @implicit.modifiers) @implicit.function,
          (class_definition
            modifiers: (modifiers
              (modifier) @implicit.modifier
              (#eq? @implicit.modifier "implicit")) @implicit.modifiers) @implicit.class,
          (parameter
            modifiers: (modifiers
              (modifier) @implicit.modifier
              (#eq? @implicit.modifier "implicit")) @implicit.modifiers) @implicit.param
        ]
    """,
    # Annotation patterns
    "annotation": """\
        [
          (annotation
            name: (identifier) @annotation.name
            arguments: (argument_list)? @annotation.args) @annotation
        ]
    """,
    # Documentation patterns
    "documentation": """\
        [
          (comment) @doc.line,
          (multi_line_comment) @doc.block,
          (scaladoc) @doc.scaladoc
        ]
    """
}

GROOVY_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (method_declaration)
          (closure_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
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
    "function": """\
        [
          (definition)
          (lambda_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
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
    "function": """\
        [
          (defn_declaration)
          (anonymous_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
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
    "function": """\
        [
          (function_declaration)
          (anonymous_function)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
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
    "function": """\
        [
          (function_definition)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (function_definition
             name: (identifier) @function.name
             parameters: (parameter_block)? @function.params
            body: (script_block) @function.body) @function.def
        ]
    """
}

CSHARP_PATTERNS = {
    # Basic pattern for function detection
    "function": """\
        [
          (method_declaration)
          (constructor_declaration)
          (local_function_statement)
          (anonymous_method_expression)
          (lambda_expression)
        ] @function
    """,
    # Extended pattern for detailed function information
    "function_details": """\
        [
          (method_declaration
            modifiers: (modifier_list)? @function.modifiers
            type: (_) @function.return_type
            name: (identifier) @function.name
            parameters: (parameter_list
              (parameter
                type: (_) @function.param.type
                name: (identifier) @function.param.name
                default_value: (_)? @function.param.default)*) @function.params
            constraints: (type_parameter_constraints_clause)? @function.constraints
            body: (block) @function.body
            [
              (documentation_comment)* @function.doc
            ]?) @function.def,
          (constructor_declaration
            modifiers: (modifier_list)? @function.modifiers
            name: (identifier) @function.name
            parameters: (parameter_list) @function.params
            initializer: (constructor_initializer)? @function.initializer
            body: (block) @function.body) @function.def,
          (local_function_statement
            modifiers: (modifier_list)? @function.modifiers
            type: (_) @function.return_type
            name: (identifier) @function.name
            parameters: (parameter_list) @function.params
            body: (block) @function.body) @function.def
        ]
    """,
    # Class patterns
    "class": """\
        [
          (class_declaration)
          (interface_declaration)
          (struct_declaration)
          (record_declaration)
        ] @class
    """,
    "class_details": """\
        [
          (class_declaration
            modifiers: (modifier_list)? @class.modifiers
            name: (identifier) @class.name
            type_parameters: (type_parameter_list)? @class.type_params
            base_list: (base_list
              (base_type
                type: (identifier) @class.base)*)?
            constraints: (type_parameter_constraints_clause)? @class.constraints
            body: (declaration_list
              [
                (field_declaration)* @class.fields
                (property_declaration)* @class.properties
                (method_declaration)* @class.methods
                (constructor_declaration)* @class.constructors
              ]
              [
                (comment)* @class.doc
              ]?)) @class.def,
          (interface_declaration
            modifiers: (modifier_list)? @interface.modifiers
            name: (identifier) @interface.name
            type_parameters: (type_parameter_list)? @interface.type_params
            base_list: (base_list)? @interface.base_list
            body: (declaration_list
              [
                (property_declaration)* @interface.properties
                (method_declaration)* @interface.methods
              ])) @interface.def,
          (record_declaration
            modifiers: (modifier_list)? @record.modifiers
            name: (identifier) @record.name
            parameters: (parameter_list)? @record.params
            base_list: (base_list)? @record.base_list
            body: (declaration_list)? @record.body) @record.def
        ]
    """,
    # Namespace patterns
    "namespace": """\
        [
          (namespace_declaration
            name: (qualified_name) @namespace.name
            body: (declaration_list) @namespace.body) @namespace.def,
          (using_declaration
            name: (qualified_name) @using.name
            alias: (identifier)? @using.alias) @using
        ]
    """,
    # Type patterns
    "type": """\
        [
          (predefined_type) @type.predefined,
          (nullable_type
            type: (_) @type.inner) @type.nullable,
          (array_type
            type: (_) @type.element
            rank: (array_rank_specifier) @type.rank) @type.array,
          (generic_name
            type: (identifier) @type.generic.base
            arguments: (type_argument_list
              (_)* @type.generic.args)) @type.generic
        ]
    """,
    # LINQ patterns
    "linq": """\
        [
          (query_expression
            (from_clause
              type: (_)? @linq.from.type
              name: (identifier) @linq.from.name
              source: (_) @linq.from.source) @linq.from
            body: (query_body
              clauses: [
                (where_clause
                  condition: (_) @linq.where.condition)? @linq.where
                (orderby_clause
                  orderings: (ordering
                    expression: (_) @linq.orderby.expr
                    direction: (_)? @linq.orderby.dir)*) @linq.orderby
                (select_clause
                  expression: (_) @linq.select.expr) @linq.select
              ]) @linq.body) @linq
        ]
    """,
    # Async/await patterns
    "async": """\
        [
          (method_declaration
            modifiers: (modifier_list
              (modifier) @async.modifier
              (#eq? @async.modifier "async")) @async.modifiers) @async.method,
          (await_expression
            expression: (_) @async.awaited) @async
        ]
    """,
    # Attribute patterns
    "attribute": """\
        [
          (attribute_list
            (attribute
              name: (identifier) @attribute.name
              arguments: (attribute_argument_list
                (attribute_argument
                  name: (identifier)? @attribute.arg.name
                  expression: (_) @attribute.arg.value)*) @attribute.args)) @attribute,
          (global_attribute_list
            (global_attribute
              target: (identifier) @attribute.global.target
              attribute: (attribute) @attribute.global.attr)) @attribute.global
        ]
    """,
    # Event patterns
    "event": """\
        [
          (event_declaration
            modifiers: (modifier_list)? @event.modifiers
            type: (_) @event.type
            name: (identifier) @event.name
            accessors: (accessor_list)? @event.accessors) @event,
          (event_field_declaration
            modifiers: (modifier_list)? @event.field.modifiers
            type: (_) @event.field.type
            declarators: (variable_declarator
              name: (identifier) @event.field.name)*) @event.field
        ]
    """,
    # Property patterns
    "property": """\
        [
          (property_declaration
            modifiers: (modifier_list)? @property.modifiers
            type: (_) @property.type
            name: (identifier) @property.name
            accessors: (accessor_list
              [
                (get_accessor_declaration)? @property.get
                (set_accessor_declaration)? @property.set
              ]) @property.accessors) @property,
          (auto_property_declaration
            modifiers: (modifier_list)? @property.auto.modifiers
            type: (_) @property.auto.type
            name: (identifier) @property.auto.name
            value: (_)? @property.auto.value) @property.auto
        ]
    """,
    # Documentation patterns
    "documentation": """\
        [
          (documentation_comment) @doc.xml,
          (single_line_comment) @doc.line,
          (multiline_comment) @doc.block
        ]
    """
}