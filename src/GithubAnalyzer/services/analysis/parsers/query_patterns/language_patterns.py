"""Language-specific query patterns for tree-sitter parsers.

This module exports hard-coded patterns for specific languages such as Python, C, YAML, and JavaScript/TypeScript variants.
"""

PYTHON_PATTERNS = {
    "function": """\
        [
          (function_definition)
          (lambda)
        ] @function
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
    """
}

C_PATTERNS = {
    "function": """\
        [
          (function_definition)
        ] @function
    """
}

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

JS_VARIANT_PATTERNS = {
    "javascript": {
        "function": """\
            [
              (function_declaration)
              (function_expression)
              (arrow_function)
              (method_definition)
            ] @function
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
        "function": """\
            [
              (function_declaration)
              (function_expression)
              (arrow_function)
              (method_definition)
            ] @function
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

# More languages or additional patterns can be added as needed...

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
};

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
};

# End of extended language patterns 

# ------------------------------------------------------------
# Extended patterns for additional common languages
# ------------------------------------------------------------

JAVA_PATTERNS = {
    "function": """\
        [
          (method_declaration)
          (constructor_declaration)
        ] @function
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
    """
};

GO_PATTERNS = {
    "function": """\
        (function_declaration
           name: (identifier) @function.name
           parameters: (parameter_list) @function.params
           body: (block) @function.body) @function
    """,
    "import": """\
        (import_declaration
           (import_specifier) @import) @import
    """,
    "variable": """\
        (short_var_declaration
           left: (identifier) @variable.name
           right: (_) @variable.value) @variable
    """,
    "conditional": """\
        (if_statement
           condition: (expression) @conditional.condition
           consequence: (block) @conditional.consequence
           (else_clause (block) @conditional.alternative)?) @conditional
    """,
    "loop": """\
        [
          (for_statement
            (range_clause)? @loop.range
            body: (block) @loop.body),
          (while_statement
            condition: (expression) @loop.condition
            body: (block) @loop.body)
        ] @loop
    """
};

RUST_PATTERNS = {
    "function": """\
        (function_item
           name: (identifier) @function.name
           parameters: (parameters) @function.params
           body: (block) @function.body) @function
    """,
    "import": """\
        (use_declaration
           (scoped_identifier) @import.name) @import
    """,
    "variable": """\
        (let_declaration
           (pattern) @variable.name
           value: (_) @variable.value) @variable
    """,
    "conditional": """\
        (if_expression
           condition: (expression) @conditional.condition
           consequence: (block) @conditional.consequence
           (else_clause (block) @conditional.alternative)?) @conditional
    """,
    "loop": """\
        [
          (for_expression
            pattern: (identifier) @loop.pattern
            iterator: (expression) @loop.iterator
            body: (block) @loop.body),
          (while_expression
            condition: (expression) @loop.condition
            body: (block) @loop.body)
        ] @loop
    """
};

CPP_PATTERNS = {
    "function": """\
        (function_definition
           declarator: (function_declarator
                        name: (identifier) @function.name)
           body: (compound_statement) @function.body) @function
    """,
    "import": """\
        (preproc_include
           path: (string_literal) @import.path) @import
    """,
    "variable": """\
        (init_declarator
           declarator: (identifier) @variable.name
           initializer: (initializer_clause)? @variable.value) @variable
    """,
    "conditional": """\
        (if_statement
           condition: (expression) @conditional.condition
           then: (compound_statement) @conditional.consequence
           (else_clause (compound_statement) @conditional.alternative)?) @conditional
    """,
    "loop": """\
        [
          (for_statement
           (for_init_statement)? @loop.init
           condition: (expression)? @loop.condition
           (for_update_statement)? @loop.update
           body: (compound_statement) @loop.body),
          (while_statement
           condition: (expression) @loop.condition
           body: (compound_statement) @loop.body)
        ] @loop
    """
};

RUBY_PATTERNS = {
    "function": """\
        [
          (method) @function,
          (singleton_method) @function
        ] @function
    """,
    "import": """\
        (call
           function: (identifier) @import.require
           arguments: (argument_list (string) @import.source)) @import
    """,
    "variable": """\
        (assignment
           left: (identifier) @variable.name
           right: (_) @variable.value) @variable
    """,
    "conditional": """\
        (if
           condition: (expression) @conditional.condition
           consequence: (compound_statement) @conditional.consequence
           (else (compound_statement) @conditional.alternative)?) @conditional
    """,
    "loop": """\
        (for
           variable: (identifier) @loop.variable
           collection: (expression) @loop.collection
           body: (compound_statement) @loop.body) @loop
    """
};

PHP_PATTERNS = {
    "function": """\
        (function_definition
           name: (identifier) @function.name
           parameters: (formal_parameter_list) @function.params
           body: (compound_statement) @function.body) @function
    """,
    "import": """\
        [
          (include_once_statement (string) @import.path) @import,
          (require_once_statement (string) @import.path) @import
        ]
    """,
    "variable": """\
        (assignment_expression
           left: (variable_name) @variable.name
           right: (_) @variable.value) @variable
    """,
    "conditional": """\
        (if_statement
           condition: (parenthesized_expression)? @conditional.condition
           statement: (compound_statement) @conditional.consequence
           (else_clause (compound_statement) @conditional.alternative)?) @conditional
    """,
    "loop": """\
        [
          (for_statement
            (for_initializer)? @loop.init
            condition: (parenthesized_expression)? @loop.condition
            (for_update)? @loop.update
            statement: (compound_statement) @loop.body),
          (while_statement
            condition: (parenthesized_expression)? @loop.condition
            statement: (compound_statement) @loop.body)
        ] @loop
    """
};

SWIFT_PATTERNS = {
    "function": """\
        (function_declaration
           signature: (function_signature
                        name: (identifier) @function.name
                        parameters: (parameter_clause) @function.params)
           body: (code_block) @function.body) @function
    """,
    "import": """\
        (import_declaration
           module: (identifier) @import.module) @import
    """,
    "variable": """\
        (variable_declaration
           pattern: (identifier) @variable.name
           initializer: (initializer_clause)? @variable.value) @variable
    """,
    "conditional": """\
        (if_statement
           condition: (expression) @conditional.condition
           body: (code_block) @conditional.consequence
           (else_clause (code_block) @conditional.alternative)?) @conditional
    """,
    "loop": """\
        [
          (for_in_statement
            pattern: (identifier) @loop.variable
            sequence: (expression) @loop.sequence
            body: (code_block) @loop.body),
          (while_statement
            condition: (expression) @loop.condition
            body: (code_block) @loop.body)
        ] @loop
    """
};

KOTLIN_PATTERNS = {
    "function": """\
        (function_declaration
           name: (simple_identifier) @function.name
           value_parameters: (value_parameter_list) @function.params
           body: (block) @function.body) @function
    """,
    "import": """\
        (import_directive
           imported_declaration: (user_type)? @import) @import
    """,
    "variable": """\
        (property_declaration
           name: (simple_identifier) @variable.name
           initializer: (expression)? @variable.value) @variable
    """,
    "conditional": """\
        (if_expression
           condition: (expression) @conditional.condition
           then: (block) @conditional.consequence
           (else: (block) @conditional.alternative)?) @conditional
    """,
    "loop": """\
        [
          (for_expression
            loop_range: (expression) @loop.range
            body: (block) @loop.body),
          (while_expression
            condition: (expression) @loop.condition
            body: (block) @loop.body)
        ] @loop
    """
};

# End of extended patterns for additional common languages 

# ------------------------------------------------------------
# Extended HTML patterns
# ------------------------------------------------------------

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
                ]?)* @element.attrs)
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
                ]?)* @element.attrs)) @element.self_closing
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

# End of extended HTML patterns 

# Extended patterns for Bash, Dart, and Elixir

BASH_PATTERNS = {
    "function": """
        [
          (function_definition
            name: (word) @function.name
            body: (compound_command) @function.body) @function.def
          (function_definition
            name: (word) @function.name
            body: (command) @function.body) @function.def
        ]
    """,
    "variable": """
        (assignment_statement
            left: (word) @variable.name
            right: (word) @variable.value) @variable
    """
}

DART_PATTERNS = {
    "function": """
        [
          (function_signature
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def
          (method_signature
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def
          (constructor_signature
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def
          (function_expression
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def
        ]
    """,
    "import": """
        [
          (import_directive
            uri: (string) @import.source) @import
        ]
    """
}

ELIXIR_PATTERNS = {
    "function": """
        [
          (call
            target: (identifier) @def.keyword
            (#match? @def.keyword "^(def|defp|defmacro)$")
            (_) @function.name
            (_)* @function.body) @function.def
          (anonymous_function
            (identifier)? @function.name
            (_) @function.args
            (_) @function.body) @function.def
        ]
    """,
    "module": """
        (module
          name: (alias) @module.name
          body: (do_block) @module.body) @module.def
    """
}

# ------------------------------------------------------------
# Extended patterns for additional languages
# ------------------------------------------------------------

ADA_PATTERNS = {
    "function": """
        [
          (subprogram_body
             (procedure_specification
                name: (identifier)? @function.name)
             body: (block) @function.body) @function,
          (subprogram_body
             (function_specification
                name: (identifier)? @function.name)
             body: (block) @function.body) @function
        ]
    """
}

HASKELL_PATTERNS = {
    "function": """
        [
          (function_declaration
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
             body: (expression) @function.body) @function,
          (lambda_expression
             parameters: (parameter_list)? @function.params
             body: (expression) @function.body) @function
        ]
    """,
    "import": """
        (import_declaration 
            module: (module_name) @import.name) @import
    """
}

PERL_PATTERNS = {
    "function": """
        [
          (subroutine_definition
             name: (identifier) @function.name
             body: (block) @function.body) @function
        ]
    """,
    "variable": """
        (assignment
           left: (scalar_variable) @variable.name
           right: (_) @variable.value) @variable
    """
}

OBJECTIVEC_PATTERNS = {
    "function": """
        [
          (method_declaration
             receiver: (object)?
             selector: (selector) @function.name
             parameters: (parameter_list)? @function.params
             body: (compound_statement) @function.body) @function
        ]
    """
}

LUA_PATTERNS = {
    "function": """
        [
          (function_declaration
             name: (identifier)? @function.name
             parameters: (parameter_list)? @function.params
             body: (block) @function.body) @function,
          (local_function
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
             body: (block) @function.body) @function
        ]
    """
}

SCALA_PATTERNS = {
    "function": """
        [
          (function_definition
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
             body: (block) @function.body) @function,
          (method_definition
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
             body: (block) @function.body) @function
        ]
    """,
    "import": """
        (import_statement
            imported: (identifier) @import.name) @import
    """
}

GROOVY_PATTERNS = {
    "function": """
        [
          (method_declaration
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
             body: (block) @function.body) @function,
          (closure_expression
             parameters: (parameter_list)? @function.params
             body: (block) @function.body) @function
        ]
    """
}

RACKET_PATTERNS = {
    "function": """
        [
          (definition
             name: (identifier) @function.name
             body: (expression) @function.body) @function,
          (lambda_expression
             parameters: (list) @function.params
             body: (expression) @function.body) @function
        ]
    """
}

CLOJURE_PATTERNS = {
    "function": """
        [
          (defn_declaration
             name: (symbol) @function.name
             parameters: (vector) @function.params
             body: (expression) @function.body) @function,
          (anonymous_function
             parameters: (vector) @function.params
             body: (expression) @function.body) @function
        ]
    """
}

SQUIRREL_PATTERNS = {
    "function": """
        [
          (function_declaration
             name: (identifier) @function.name
             parameters: (parameter_list)? @function.params
             body: (block) @function.body) @function,
          (anonymous_function
             parameters: (parameter_list)? @function.params
             body: (block) @function.body) @function
        ]
    """
}

POWERSHELL_PATTERNS = {
    "function": """
        [
          (function_definition
             name: (identifier) @function.name
             parameters: (parameter_block)? @function.params
             body: (script_block) @function.body) @function
        ]
    """
}