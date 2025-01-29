from typing import Dict, Optional, Any, Tuple, Union
"""Query patterns for tree-sitter.

Contains predefined patterns for common code elements and their optimization settings.
"""
from dataclasses import dataclass

# Mapping of file extensions to tree-sitter language names
EXTENSION_TO_LANGUAGE = {
    # Web Technologies
    'js': 'javascript',
    'jsx': 'javascript',
    'mjs': 'javascript',
    'cjs': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'mts': 'typescript',
    'cts': 'typescript',
    'html': 'html',
    'htm': 'html',
    'css': 'css',
    'scss': 'scss',
    'sass': 'scss',
    'less': 'css',
    'vue': 'vue',
    'svelte': 'svelte',
    
    # Systems Programming
    'c': 'c',
    'h': 'c',
    'cpp': 'cpp',
    'hpp': 'cpp',
    'cc': 'cpp',
    'cxx': 'cpp',
    'hxx': 'cpp',
    'h++': 'cpp',
    'cu': 'cuda',
    'cuh': 'cuda',
    'rs': 'rust',
    'go': 'go',
    'mod': 'gomod',
    'sum': 'gosum',
    
    # JVM Languages
    'java': 'java',
    'kt': 'kotlin',
    'kts': 'kotlin',
    'scala': 'scala',
    'sc': 'scala',
    'groovy': 'groovy',
    'gradle': 'groovy',
    
    # Scripting Languages
    'py': 'python',
    'pyi': 'python',
    'pyc': 'python',
    'pyd': 'python',
    'pyw': 'python',
    'rb': 'ruby',
    'rbw': 'ruby',
    'rake': 'ruby',
    'gemspec': 'ruby',
    'php': 'php',
    'php4': 'php',
    'php5': 'php',
    'php7': 'php',
    'php8': 'php',
    'phps': 'php',
    'lua': 'lua',
    'pl': 'perl',
    'pm': 'perl',
    't': 'perl',
    
    # Shell Scripting
    'sh': 'bash',
    'bash': 'bash',
    'zsh': 'bash',
    'fish': 'fish',
    'ksh': 'bash',
    'csh': 'bash',
    'tcsh': 'bash',
    
    # Functional Languages
    'hs': 'haskell',
    'lhs': 'haskell',
    'ml': 'ocaml',
    'mli': 'ocaml',
    'ex': 'elixir',
    'exs': 'elixir',
    'heex': 'heex',
    'clj': 'clojure',
    'cljs': 'clojure',
    'cljc': 'clojure',
    'edn': 'clojure',
    
    # Configuration & Data
    'yaml': 'yaml',
    'yml': 'yaml',
    'json': 'json',
    'jsonc': 'json',
    'toml': 'toml',
    'xml': 'xml',
    'xsl': 'xml',
    'xslt': 'xml',
    'svg': 'xml',
    'xaml': 'xml',
    'ini': 'ini',
    'cfg': 'ini',
    'conf': 'ini',
    
    # Build Systems
    'cmake': 'cmake',
    'make': 'make',
    'mk': 'make',
    'ninja': 'ninja',
    'bazel': 'starlark',
    'bzl': 'starlark',
    'BUILD': 'starlark',
    'WORKSPACE': 'starlark',
    
    # Documentation
    'md': 'markdown',
    'markdown': 'markdown',
    'rst': 'rst',
    'tex': 'latex',
    'latex': 'latex',
    'adoc': 'asciidoc',
    'asciidoc': 'asciidoc',
    
    # Other Languages
    'swift': 'swift',
    'dart': 'dart',
    'r': 'r',
    'rmd': 'r',
    'jl': 'julia',
    'v': 'verilog',
    'vh': 'verilog',
    'vhd': 'vhdl',
    'vhdl': 'vhdl',
    'zig': 'zig',
    
    # Query Languages
    'sql': 'sql',
    'mysql': 'sql',
    'pgsql': 'sql',
    'graphql': 'graphql',
    'gql': 'graphql',
    
    # Additional Languages
    'proto': 'protobuf',
    'thrift': 'thrift',
    'wasm': 'wasm',
    'wat': 'wat',
    'glsl': 'glsl',
    'hlsl': 'hlsl',
    'wgsl': 'wgsl',
    'dockerfile': 'dockerfile',
    'Dockerfile': 'dockerfile',
    'nginx.conf': 'nginx',
    'rules': 'udev',
    'hypr': 'hyprlang',
    'kdl': 'kdl',
    'ron': 'ron'
}

# Special filename mappings
SPECIAL_FILENAMES = {
    # Docker
    'dockerfile': 'dockerfile',
    'Dockerfile': 'dockerfile',
    'Dockerfile.dev': 'dockerfile',
    'Dockerfile.prod': 'dockerfile',
    
    # Build systems
    'makefile': 'make',
    'Makefile': 'make',
    'CMakeLists.txt': 'cmake',
    'meson.build': 'meson',
    'BUILD': 'starlark',
    'BUILD.bazel': 'starlark',
    'WORKSPACE': 'starlark',
    'WORKSPACE.bazel': 'starlark',
    'BUCK': 'starlark',
    
    # Git
    '.gitignore': 'gitignore',
    '.gitattributes': 'gitattributes',
    '.gitmodules': 'gitconfig',
    '.gitconfig': 'gitconfig',
    
    # Shell
    '.bashrc': 'bash',
    '.zshrc': 'bash',
    '.bash_profile': 'bash',
    '.profile': 'bash',
    '.zprofile': 'bash',
    
    # Python
    'requirements.txt': 'requirements',
    'constraints.txt': 'requirements',
    'Pipfile': 'toml',
    'pyproject.toml': 'toml',
    'poetry.lock': 'toml',
    'setup.py': 'python',
    'setup.cfg': 'ini',
    'tox.ini': 'ini',
    
    # JavaScript/Node
    'package.json': 'json',
    'package-lock.json': 'json',
    'tsconfig.json': 'json',
    '.eslintrc': 'json',
    '.eslintrc.json': 'json',
    '.eslintrc.js': 'javascript',
    '.prettierrc': 'json',
    '.prettierrc.json': 'json',
    '.prettierrc.js': 'javascript',
    
    # Rust
    'Cargo.toml': 'toml',
    'Cargo.lock': 'toml',
    
    # Editor/IDE
    '.editorconfig': 'properties',
    '.vscode/settings.json': 'json',
    '.idea/workspace.xml': 'xml',
    
    # Environment/Config
    '.env': 'properties',
    '.env.local': 'properties',
    '.env.development': 'properties',
    '.env.production': 'properties',
    
    # Other
    'XCompose': 'xcompose',
    '.luacheckrc': 'lua',
    '.styluarc': 'lua',
    'CHANGELOG.md': 'markdown',
    'README.md': 'markdown',
    'LICENSE': 'text',
    'Procfile': 'properties',
    'docker-compose.yml': 'yaml',
    'docker-compose.yaml': 'yaml'
}

@dataclass
class QueryOptimizationSettings:
    """Settings for optimizing query execution."""
    match_limit: Optional[int] = None  # Maximum number of in-progress matches
    max_start_depth: Optional[int] = None  # Maximum start depth for query
    timeout_micros: Optional[int] = None  # Maximum duration in microseconds
    byte_range: Optional[Tuple[int, int]] = None  # Limit query to byte range
    point_range: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None  # Limit query to point range

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

# TypeScript-specific patterns
TS_PATTERNS = {
    "interface": """
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
          ]*) @interface.body) @interface.def
    """,
    "type": """
        [
          ; Type alias
          (type_alias_declaration
            name: (type_identifier) @type.name
            value: (_) @type.value) @type.def
            
          ; Union type
          (union_type
            types: (type_list) @type.union.types) @type.union
            
          ; Intersection type
          (intersection_type
            types: (type_list) @type.intersection.types) @type.intersection
            
          ; Generic type
          (generic_type
            name: (type_identifier) @type.generic.name
            arguments: (type_arguments
              (type_identifier) @type.generic.arg)*) @type.generic
        ]
    """,
    "enum": """
        (enum_declaration
          name: (identifier) @enum.name
          body: (enum_body
            (enum_member
              name: (property_identifier) @enum.member.name
              value: (_)? @enum.member.value)*) @enum.body) @enum.def
    """,
    "decorator": """
        (decorator
          name: [
            (identifier) @decorator.name
            (call_expression
              function: (identifier) @decorator.name
              arguments: (arguments) @decorator.args)
          ]) @decorator
    """
}

# Query patterns by language with assertions and settings
QUERY_PATTERNS = {
    "python": {
        "function": """
            (function_definition
              name: (identifier) @function.name
              parameters: (parameters) @function.params
              body: (block) @function.body
              return_type: (type)? @function.return_type
              decorators: (decorator_list)? @function.decorators) @function.def
        """,
        "class": """
            (class_definition
              name: (identifier) @class.name
              body: (block) @class.body
              superclasses: (argument_list)? @class.superclasses
              decorators: (decorator_list)? @class.decorators) @class.def
        """,
        "method": """
            (class_definition
              body: (block 
                (function_definition) @method.def
                  name: (identifier) @method.name
                  parameters: (parameters 
                    (identifier) @method.self) @method.params
                  body: (block) @method.body
                  decorators: (decorator_list)? @method.decorators)
              (#eq? @method.self "self"))
        """,
        "call": """
            (call
              function: [
                (identifier) @call.name
                (attribute 
                  object: (_) @call.object
                  attribute: (identifier) @call.method)
              ]
              arguments: (argument_list) @call.args) @call
        """,
        "import": """
            [
              (import_from_statement
                module_name: (dotted_name) @import.module
                name: (dotted_name) @import.name) @import.from
              (import_statement 
                name: (dotted_name) @import.module) @import.direct
            ] @import
            (#is-not? @import.module "__future__")
        """,
        "attribute": """
            (attribute
              object: (_) @attribute.object
              attribute: (identifier) @attribute.name) @attribute
        """,
        "string": """
            [
              (string) @string.complete
              (string_content) @string.content
              (formatted_string
                interpolation: (formatted_string_content) @string.interpolation) @string.formatted
            ] @string
        """,
        "comment": """
            [
              (comment) @comment.line
              ((comment) @comment.docstring
                (#match? @comment.docstring "^\\s*\"\"\""))
            ] @comment
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
    },
    "javascript": {
        "function": """
            [
              (function_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params
                body: (statement_block) @function.body) @function.def
              (arrow_function
                parameters: (formal_parameters) @function.params
                body: [
                  (statement_block) @function.body
                  (expression) @function.body
                ]) @function.def
            ]
        """,
        "class": """
            (class_declaration
              name: (identifier) @class.name
              body: (class_body) @class.body
              extends: (extends_clause)? @class.extends) @class.def
        """,
        "method": """
            (method_definition
              name: (property_identifier) @method.name
              parameters: (formal_parameters) @method.params
              body: (statement_block) @method.body) @method.def
        """,
        "import": """
            [
              (import_statement
                source: (string) @import.source
                clause: [
                  (import_clause
                    (identifier) @import.default)
                  (named_imports
                    (import_specifier
                      name: (identifier) @import.name)) 
                ]) @import
              (require_call
                arguments: (arguments (string) @import.source)) @import.require
            ]
        """
    },
    "typescript": {
        "function": """
            [
              (function_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params
                return_type: (type_annotation)? @function.return_type
                body: (statement_block) @function.body) @function.def
              (arrow_function
                parameters: (formal_parameters) @function.params
                return_type: (type_annotation)? @function.return_type
                body: [
                  (statement_block) @function.body
                  (expression) @function.body
                ]) @function.def
            ]
        """,
        "interface": """
            (interface_declaration
              name: (type_identifier) @interface.name
              extends_clause: (extends_type_clause)? @interface.extends
              body: (object_type) @interface.body) @interface.def
        """,
        "type": """
            (type_alias_declaration
              name: (type_identifier) @type.name
              value: (_) @type.value) @type.def
        """
    },
    "java": {
        "class": """
            (class_declaration
              name: (identifier) @class.name
              superclass: (superclass)? @class.superclass
              interfaces: (super_interfaces)? @class.interfaces
              body: (class_body) @class.body) @class.def
        """,
        "method": """
            (method_declaration
              modifiers: (modifiers)? @method.modifiers
              type: (_) @method.return_type
              name: (identifier) @method.name
              parameters: (formal_parameters) @method.params
              body: (block) @method.body) @method.def
        """,
        "interface": """
            (interface_declaration
              name: (identifier) @interface.name
              extends: (extends_interfaces)? @interface.extends
              body: (interface_body) @interface.body) @interface.def
        """
    },
    "go": {
        "function": """
            (function_declaration
              name: (identifier) @function.name
              parameters: (parameter_list) @function.params
              result: [
                (parameter_list) @function.return
                (type_identifier) @function.return
              ]?
              body: (block) @function.body) @function.def
        """,
        "struct": """
            (type_declaration
              (type_spec
                name: (type_identifier) @struct.name
                type: (struct_type
                  fields: (field_declaration_list) @struct.fields))) @struct.def
        """,
        "interface": """
            (type_declaration
              (type_spec
                name: (type_identifier) @interface.name
                type: (interface_type
                  methods: (method_spec_list) @interface.methods))) @interface.def
        """
    },
    "rust": {
        "function": """
            (function_item
              name: (identifier) @function.name
              parameters: (parameters) @function.params
              return_type: (type_identifier)? @function.return_type
              body: (block) @function.body) @function.def
        """,
        "struct": """
            (struct_item
              name: (type_identifier) @struct.name
              fields: (field_declaration_list) @struct.fields) @struct.def
        """,
        "impl": """
            (impl_item
              type: (type_identifier) @impl.type
              trait: (type_identifier)? @impl.trait
              body: (declaration_list) @impl.body) @impl.def
        """
    },
    "cpp": {
        "function": """
            (function_definition
              declarator: (function_declarator
                declarator: (identifier) @function.name
                parameters: (parameter_list) @function.params)
              type: (_) @function.return_type
              body: (compound_statement) @function.body) @function.def
        """,
        "class": """
            (class_specifier
              name: (type_identifier) @class.name
              bases: (base_class_clause)? @class.bases
              body: (field_declaration_list) @class.body) @class.def
        """,
        "namespace": """
            (namespace_definition
              name: (identifier) @namespace.name
              body: (declaration_list) @namespace.body) @namespace.def
        """
    },
    "jsx": {
        **JS_TS_SHARED_PATTERNS,
        "jsx_element": JS_TS_SHARED_PATTERNS["jsx_element"]
    },
    "tsx": {
        **JS_TS_SHARED_PATTERNS,
        **TS_PATTERNS,
        "jsx_element": JS_TS_SHARED_PATTERNS["jsx_element"]
    },
    "bash": {
        "function": """
            (function_definition
              name: (word) @function.name
              body: (compound_statement) @function.body) @function.def
        """,
        "command": """
            (command
              name: (command_name) @command.name
              argument: (command_argument)* @command.args) @command
        """,
        "variable": """
            (variable_assignment
              name: (variable_name) @variable.name
              value: (_) @variable.value) @variable
        """
    },
    "html": {
        "element": """
            (element
              tag_name: (_) @element.tag
              attribute: (attribute
                name: (_) @element.attr.name
                value: (_)? @element.attr.value)*
              text: (text)* @element.text) @element
        """
    },
    "css": {
        "rule": """
            (rule_set
              selectors: (selectors) @rule.selectors
              block: (block) @rule.block) @rule
        """,
        "property": """
            (declaration
              name: (property_name) @property.name
              value: (property_value) @property.value) @property
        """
    },
    "scala": {
        "function": """
            (function_definition
              name: (identifier) @function.name
              parameters: (parameters) @function.params
              body: (block) @function.body) @function.def
        """
    },
    "ruby": {
        "function": """
            (method
              name: (identifier) @function.name
              parameters: (method_parameters)? @function.params
              body: (body_statement) @function.body) @function.def
        """
    },
    "swift": {
        "function": """
            (function_declaration
              name: (identifier) @function.name
              parameters: (parameter_clause) @function.params
              body: (code_block) @function.body) @function.def
        """
    },
    "kotlin": {
        "function": """
            (function_declaration
              name: (simple_identifier) @function.name
              parameters: (parameter_list) @function.params
              body: (function_body) @function.body) @function.def
        """
    },
    "json": {
        "object": """
            (object
              (pair
                key: (string) @object.key
                value: (_) @object.value)*) @object
        """
    },
    "yaml": {
        "mapping": """
            (block_mapping_pair
              key: (_) @mapping.key
              value: (_) @mapping.value) @mapping
        """
    },
    "toml": {
        "table": """
            (table
              header: (table_header) @table.header
              entries: (pair
                key: (_) @table.key
                value: (_) @table.value)*) @table
        """
    },
    "xml": {
        "element": """
            (element
              tag_name: (_) @element.tag
              attribute: (attribute
                name: (_) @element.attr.name
                value: (_)? @element.attr.value)*
              text: (text)* @element.text) @element
        """
    },
    "markdown": {
        "heading": """
            (atx_heading
              marker: (_) @heading.marker
              content: (_) @heading.content) @heading
        """,
        "list": """
            (list
              item: (list_item
                content: (_) @list.item.content)*) @list
        """
    },
    "text": {
        "line": """
            (line) @line
        """
    },
    "rst": {
        "directive": """
            (directive
              name: (_) @directive.name
              content: (_) @directive.content) @directive
        """
    },
    "org": {
        "heading": """
            (heading
              stars: (_) @heading.level
              content: (_) @heading.content) @heading
        """
    },
    "ini": {
        "section": """
            (section
              name: (_) @section.name
              entries: (entry
                key: (_) @section.key
                value: (_) @section.value)*) @section
        """
    },
    "lua": {
        "function": """
            (function_definition
              name: (_) @function.name
              parameters: (parameters) @function.params
              body: (block) @function.body) @function.def
        """
    },
    "r": {
        "function": """
            (function_definition
              name: (identifier) @function.name
              parameters: (formal_parameters) @function.params
              body: (expression_list) @function.body) @function.def
        """
    },
    "elm": {
        "function": """
            (value_declaration
              name: (lower_case_identifier) @function.name
              parameters: (pattern)* @function.params
              body: (expression) @function.body) @function.def
        """
    },
    "elixir": {
        "function": """
            (function
              name: (identifier) @function.name
              parameters: (parameters) @function.params
              body: (do_block) @function.body) @function.def
        """
    },
    "erlang": {
        "function": """
            (function
              name: (atom) @function.name
              clauses: (function_clause)* @function.clauses) @function.def
        """
    },
    "haskell": {
        "function": """
            (function
              name: (variable) @function.name
              parameters: (patterns) @function.params
              body: (rhs) @function.body) @function.def
        """
    },
    "ocaml": {
        "function": """
            (let_binding
              pattern: (value_name) @function.name
              parameters: (parameter)* @function.params
              body: (expression) @function.body) @function.def
        """
    },
    "perl": {
        "subroutine": """
            (subroutine_declaration
              name: (identifier) @function.name
              body: (block) @function.body) @function.def
        """
    },
    "protobuf": {
        "message": """
            (message
              name: (identifier) @message.name
              body: (message_body) @message.body) @message.def
        """
    },
    "sql": {
        "select": """
            (select_statement
              columns: (select_expression_list) @select.columns
              from: (from_clause) @select.from
              where: (where_clause)? @select.where) @select
        """
    },
    "vue": {
        "template": """
            (template_element
              content: (_) @template.content) @template
        """,
        "script": """
            (script_element
              content: (_) @script.content) @script
        """
    },
    "zig": {
        "function": """
            (function_declaration
              name: (identifier) @function.name
              parameters: (parameter_list) @function.params
              body: (block) @function.body) @function.def
        """
    }
}

# Common patterns that apply to most languages
COMMON_PATTERNS = {
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

# Add common patterns to all languages
for language in QUERY_PATTERNS:
    QUERY_PATTERNS[language].update({
        pattern_type: pattern
        for pattern_type, pattern in COMMON_PATTERNS.items()
        if pattern_type not in QUERY_PATTERNS[language]
    })

# Default optimization settings by pattern type
DEFAULT_OPTIMIZATIONS = {
    "function": QueryOptimizationSettings(
        match_limit=100,
        max_start_depth=5,
        timeout_micros=1000
    ),
    "class": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=3,
        timeout_micros=1000
    ),
    "method": QueryOptimizationSettings(
        match_limit=200,
        max_start_depth=6,
        timeout_micros=1000
    ),
    "import": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=2,
        timeout_micros=500
    ),
    "interface": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=3,
        timeout_micros=1000
    ),
    "struct": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=3,
        timeout_micros=1000
    ),
    "namespace": QueryOptimizationSettings(
        match_limit=30,
        max_start_depth=2,
        timeout_micros=500
    ),
    "comment": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=10,
        timeout_micros=1000
    ),
    "string": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=10,
        timeout_micros=1000
    ),
    "error": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=20,
        timeout_micros=5000
    )
}

# Add language variants
JS_VARIANTS = {"javascript", "jsx", "typescript", "tsx"}

# Update get_query_pattern to handle variants
def get_query_pattern(language: str, pattern_type: str) -> Optional[str]:
    """Get query pattern for language and type.
    
    Args:
        language: Language identifier
        pattern_type: Type of pattern to get
        
    Returns:
        Query pattern string or None if not found
    """
    if language not in QUERY_PATTERNS:
        # Try to get pattern from base language
        base_lang = get_base_language(language)
        if base_lang != language and base_lang in QUERY_PATTERNS:
            return QUERY_PATTERNS[base_lang].get(pattern_type)
        return None
    return QUERY_PATTERNS[language].get(pattern_type)

# Update get_optimization_settings to handle variants
def get_optimization_settings(pattern_type: str, language: Optional[str] = None) -> QueryOptimizationSettings:
    """Get default optimization settings for a pattern type.
    
    Args:
        pattern_type: Type of pattern
        language: Optional language identifier
        
    Returns:
        QueryOptimizationSettings with default values for the pattern
    """
    # Get base settings
    settings = DEFAULT_OPTIMIZATIONS.get(pattern_type, QueryOptimizationSettings())
    
    # Apply language-specific adjustments
    if language and is_js_variant(language):
        # Increase limits for JSX/TSX
        if language.lower() in {'jsx', 'tsx'} and pattern_type in {'function', 'class', 'jsx_element'}:
            settings.match_limit *= 2  # Double the limits for JSX/TSX
            settings.max_start_depth += 5  # Increase depth for nested elements
            
    return settings 

def is_js_variant(language: str) -> bool:
    """Check if a language is a JavaScript variant.
    
    Args:
        language: Language identifier
        
    Returns:
        True if language is a JavaScript variant
    """
    return language.lower() in JS_VARIANTS

def get_base_language(language: Optional[str]) -> str:
    """Get base language for variants.
    
    Args:
        language: Language identifier
        
    Returns:
        Base language (e.g., 'javascript' for 'jsx')
    """
    if not language:
        return "python"  # Default to Python as our primary language
        
    language = language.lower()
    if language in {'jsx', 'tsx'}:
        return 'javascript'
    elif language in {'hpp', 'cc', 'hh'}:
        return 'cpp'
    return language 