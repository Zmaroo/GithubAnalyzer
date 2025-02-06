from typing import Dict, Optional, Any, Tuple, Union
"""Query patterns for tree-sitter.

Contains predefined patterns for common code elements and their optimization settings.
"""
from dataclasses import dataclass
from GithubAnalyzer.services.analysis.parsers.custom_parsers import get_custom_parser

# JavaScript/TypeScript variants
JS_VARIANTS = {"javascript", "jsx", "typescript", "tsx"}

# Mapping of file extensions to tree-sitter language names
EXTENSION_TO_LANGUAGE = {
    # Web Technologies
    'js': 'javascript',
    'jsx': 'javascript',
    'mjs': 'javascript',
    'cjs': 'javascript',
    'es': 'javascript',
    'es6': 'javascript',
    'iife.js': 'javascript',
    'bundle.js': 'javascript',
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
    'v': 'verilog',
    'sv': 'verilog',
    'vh': 'verilog',
    'vhd': 'vhdl',
    'vhdl': 'vhdl',
    
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
    'ron': 'ron',
    'commonlisp': 'commonlisp',
    'elixir': 'elixir'
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
    'yarn.lock': 'yaml',
    'pnpm-lock.yaml': 'yaml',
    'webpack.config.js': 'javascript',
    'rollup.config.js': 'javascript',
    'babel.config.js': 'javascript',
    '.babelrc': 'json',
    '.babelrc.json': 'json',
    'tsconfig.json': 'json',
    
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

# JavaScript/TypeScript/JSX/TSX variants
JS_VARIANT_PATTERNS = {
    "javascript": {
        "function": """
            [
              (function_declaration)
              (function_expression)
              (arrow_function)
              (method_definition)
            ] @function
        """
    },
    "typescript": {
        "function": """
            [
              (function_declaration)
              (function_expression)
              (arrow_function)
              (method_definition)
            ] @function
        """
    }
}

# Pattern templates for common structures
PATTERN_TEMPLATES = {
    "basic_function": """
        ({function_type}
          name: ({name_type}) @function.name
          parameters: ({params_type}) @function.params
          body: ({body_type}) @function.body) @function.def
    """,
    "basic_class": """
        ({class_type}
          name: ({name_type}) @class.name
          {inheritance}
          body: ({body_type}) @class.body) @class.def
    """,
    "basic_method": """
        ({method_type}
          name: ({name_type}) @method.name
          parameters: ({params_type}) @method.params
          body: ({body_type}) @method.body) @method.def
    """
}

def create_function_pattern(
    function_type: str,
    name_type: str = "identifier",
    params_type: str = "formal_parameters",
    body_type: str = "statement_block"
) -> str:
    """Create a function pattern from the template.
    
    Args:
        function_type: Type of function node
        name_type: Type of name node
        params_type: Type of parameters node
        body_type: Type of body node
        
    Returns:
        Function pattern string
    """
    return PATTERN_TEMPLATES["basic_function"].format(
        function_type=function_type,
        name_type=name_type,
        params_type=params_type,
        body_type=body_type
    )

def create_class_pattern(
    class_type: str,
    name_type: str = "identifier",
    body_type: str = "class_body",
    inheritance: str = ""
) -> str:
    """Create a class pattern from the template.
    
    Args:
        class_type: Type of class node
        name_type: Type of name node
        body_type: Type of body node
        inheritance: Inheritance clause pattern
        
    Returns:
        Class pattern string
    """
    return PATTERN_TEMPLATES["basic_class"].format(
        class_type=class_type,
        name_type=name_type,
        body_type=body_type,
        inheritance=inheritance
    )

# Python-specific patterns
PYTHON_PATTERNS = {
    "function": """
        [
          (function_definition)
          (lambda)
        ] @function
    """
}

# Add C-specific patterns
C_PATTERNS = {
    "function": """
        [
          (function_definition)
        ] @function
    """
}

# Add YAML patterns
YAML_PATTERNS = {
    "mapping": """
        (block_mapping_pair
          key: (_) @mapping.key
          value: (_) @mapping.value) @mapping
    """,
    "sequence": """
        (block_sequence
          (block_sequence_item
            (_) @sequence.item)*) @sequence
    """,
    "anchor": """
        (anchor
          name: (anchor_name) @anchor.name) @anchor
    """,
    "alias": """
        (alias
          name: (alias_name) @alias.name) @alias
    """
}

# Add TOML patterns
TOML_PATTERNS = {
    "table": """
        (table
          header: (table_header) @table.header
          entries: (pair
            key: (_) @table.key
            value: (_) @table.value)*) @table
    """,
    "array": """
        (array
          value: (_)* @array.value) @array
    """,
    "inline_table": """
        (inline_table
          (pair
            key: (_) @table.key
            value: (_) @table.value)*) @inline_table
    """
}

# Add Dockerfile patterns
DOCKERFILE_PATTERNS = {
    "instruction": """
        (instruction
          cmd: (_) @instruction.cmd
          value: (_)* @instruction.value) @instruction
    """,
    "from": """
        (from_instruction
          image: (_) @from.image
          tag: (_)? @from.tag
          platform: (_)? @from.platform) @from
    """,
    "run": """
        (run_instruction
          command: (_) @run.command) @run
    """
}

# Enhance Markdown patterns
MARKDOWN_PATTERNS = {
    "heading": """
        (atx_heading
          marker: (_) @heading.marker
          content: (_) @heading.content) @heading
    """,
    "list": """
        (list
          item: (list_item
            content: (_) @list.item.content)*) @list
    """,
    "link": """
        [
          (link
            text: (_) @link.text
            url: (_) @link.url) @link
          (image
            text: (_) @image.text
            url: (_) @image.url) @image
        ]
    """,
    "code_block": """
        [
          (fenced_code_block
            language: (_)? @code.language
            content: (_) @code.content) @code.block
          (indented_code_block) @code.indented
        ]
    """,
    "blockquote": """
        (block_quote
          content: (_) @quote.content) @quote
    """
}

# Query patterns by language with assertions and settings
QUERY_PATTERNS = {
    "python": {
        "function": """
            [
              (function_definition)
              (lambda)
            ] @function
        """
    },
    **JS_VARIANT_PATTERNS,  # Add JavaScript variants
    "c": {
        "function": """
            [
              (function_definition)
            ] @function
        """
    },
    "yaml": YAML_PATTERNS,
    "toml": TOML_PATTERNS,
    "dockerfile": DOCKERFILE_PATTERNS,
    "markdown": MARKDOWN_PATTERNS,
    "java": {
        "function": """
            [
              (method_declaration)
              (constructor_declaration)
            ] @function
        """
    },
    "go": {
        "function": """
            [
              (function_declaration)
              (method_declaration)
            ] @function
        """
    },
    "rust": {
        "function": """
            [
              (function_item)
              (closure_expression)
            ] @function
        """
    },
    "cpp": {
        "function": '''
            [
              ; Regular function definitions
              (function_definition
                [
                  (primitive_type)
                  (type_identifier)
                  (placeholder_type_specifier)
                ]? @function.return_type
                (function_declarator
                  [
                    (identifier)
                    (field_identifier)
                  ] @function.name
                  (parameter_list) @function.params)
                (compound_statement) @function.body) @function.def

              ; Template functions
              (template_declaration
                (template_parameter_list) @function.template_params
                (function_definition) @function.def) @function.template

              ; Lambda expressions
              (lambda_expression
                (lambda_capture_specifier)? @function.captures
                (parameter_list)? @function.params
                (compound_statement) @function.body) @function.def

              ; Operator overloads
              (function_definition
                (function_declarator
                  (operator_name) @function.operator
                  (parameter_list) @function.params)
                (compound_statement) @function.body) @function.def

              ; Constructor/Destructor
              (function_definition
                (function_declarator
                  [
                    (identifier) @function.constructor
                    (destructor_name) @function.destructor
                  ]
                  (parameter_list) @function.params)
                (compound_statement) @function.body) @function.def

              ; Friend functions
              (friend_declaration
                (declaration
                  (function_declarator) @function.declarator)) @function.friend
            ] @function
        '''
    },
    "scala": {
        "function": """
            [
              (function_definition)
              (class_definition)
            ] @function
        """
    },
    "ruby": {
        "function": """
            [
              (method)
              (singleton_method)
            ] @function
        """
    },
    "swift": {
        "function": """
            [
              (function_declaration)
              (protocol_function_declaration)
              (lambda_function_type)
            ] @function
        """
    },
    "kotlin": {
        "function": """
            [
              (function_declaration)
              (lambda_literal)
            ] @function
        """
    },
    "lua": {
        "function": """
            [
              (function_definition)
              (function_declaration)
            ] @function
        """
    },
    "r": {
        "function": """
            [
              (function_definition)
            ] @function
        """
    },
    "hack": {
        "function": """
            [
              (method_declaration)
              (function_declaration)
              (lambda_expression)
            ] @function
        """
    },
    "gleam": {
        "function": """
            [
              (function)
              (anonymous_function)
            ] @function
        """
    },
    "haxe": {
        "function": """
            (function_declaration) @function
            (identifier) @function
        """
    },
    "pascal": {
        "function": """
            [
              (function_declaration)
              (procedure_declaration)
            ] @function
        """
    },
    "fortran": {
        "function": """
            [
              (function_definition)
              (subroutine_definition)
            ] @function
        """
    },
    "d": {
        "function": """
            [
              (function_declaration)
              (constructor_declaration)
              (destructor_declaration)
            ] @function
        """
    },
    "groovy": {
        "function": """
            (func) @function
        """
    },
    "racket": {
        "function": """
            (list
                (symbol) @def_type
                (#match? @def_type "^(define|define-syntax|λ|lambda|define/contract)$")
            ) @function
        """
    },
    "clojure": {
        "function": """
            (list_lit
                (sym_lit) @def_type
                (#match? @def_type "^(defn|defn-|defmacro|defmethod|fn)$")
            ) @function
        """
    },
    "elixir": {
        "function": '''
            (call
                target: (identifier) @def.keyword
                (#match? @def.keyword "^(def|defp|defmacro)$")
                (_) @function.name
                (_)* @function.body)
            
            (anonymous_function
                (_) @function.args
                (_) @function.body)
        '''
    },
    "haskell": {
        "function": """
            [
              (function)
              (lambda)
            ] @function
        """
    },
    "purescript": {
        "function": """
            [
              (function)
              (exp_lambda)
            ] @function
        """
    },
    "dart": {
        "function": """
            [
              (function_signature)
              (method_signature)
              (constructor_signature)
              (function_expression)
              (function_body)
            ] @function
        """
    },
    "ocaml": {
        "function": """
            [
              (let_binding)
              (let_rec_binding)
              (value_binding)
              (method_binding)
              (fun_binding)
            ] @function
        """
    },
    "tcl": {
        "function": """
            (procedure
                name: (_) @function.name
                arguments: (_) @function.args
                body: (_) @function.body)
        """
    },
    "verilog": {
        "function": """
            [
              (module_declaration) @function
              (function_declaration) @function
              (task_declaration) @function
            ]
        """
    },
    "zig": {
        "function": '''
            [
                ; Function declarations with body
                (Decl
                    (FnProto
                        function: (IDENTIFIER) @function.name
                        (ParamDeclList)? @function.params)
                    (Block) @function.body)

                ; Function prototypes
                (FnProto 
                    function: (IDENTIFIER) @function.name
                    (ParamDeclList)? @function.params)

                ; Test functions
                (TestDecl
                    (IDENTIFIER) @function.name
                    (Block) @function.body)
            ] @function
        '''
    },
    "commonlisp": {
        "function": """
            (list_lit
                value: [
                    (sym_lit) @defun.keyword
                    (#eq? @defun.keyword "defun")
                    (sym_lit) @function.name
                    (list_lit) @function.args
                    (_)* @function.body
                ])
            
            (list_lit
                value: [
                    (sym_lit) @defmethod.keyword
                    (#eq? @defmethod.keyword "defmethod")
                    (sym_lit) @function.name
                    (list_lit) @function.args
                    (_)* @function.body
                ])
            
            (list_lit
                value: [
                    (sym_lit) @defmacro.keyword
                    (#eq? @defmacro.keyword "defmacro")
                    (sym_lit) @function.name
                    (list_lit) @function.args
                    (_)* @function.body
                ])
            
            (list_lit
                value: [
                    (sym_lit) @lambda.keyword
                    (#eq? @lambda.keyword "lambda")
                    (list_lit) @function.args
                    (_)* @function.body
                ])
        """
    },
    "ada": {
        "function": """
            (subprogram_body
                (procedure_specification
                    name: (_) @function.name)
                (_)* @function.body)
            
            (subprogram_body
                (function_specification
                    name: (_) @function.name)
                (_)* @function.body)
        """
    },
    "bash": {
        "function": """
            [
              (function_definition)
              (command)
            ] @function
        """
    },
    "fish": {
        "function": """
            (function_definition) @function
        """
    },
    "erlang": {
        "function": """
            (fun_decl
                (function_clause
                    name: (atom) @function.name
                    args: (expr_args) @function.args
                    body: (clause_body) @function.body))
            
            (anonymous_fun
                (fun_clause
                    args: (expr_args) @function.args
                    body: (clause_body) @function.body))
        """
    },
    "solidity": {
        "function": """
            [
              (function_definition) @function
              (constructor_definition) @function
              (modifier_definition) @function
            ]
        """
    },
    "julia": {
        "function": '''
            [
              ; Regular function definitions
              (function_definition
                (signature
                  (call_expression
                    (identifier) @function.name
                    (argument_list) @function.params))
                (_)* @function.body) @function.def
                
              ; Macro definitions
              (macro_definition
                (signature
                  (call_expression
                    (identifier) @function.name
                    (argument_list) @function.params))
                (_)* @function.body) @function.def
                
              ; Arrow functions
              (assignment
                (identifier) @function.name
                (function_expression
                  (identifier) @function.params
                  (_) @function.body)) @function.def
                
              ; Short form function assignments
              (assignment
                (call_expression
                  (identifier) @function.name
                  (argument_list) @function.params)
                (_) @function.body) @function.def
            ] @function
        '''
    },
    "elm": {
        "function": """
            [
              ; Regular function declarations with type annotations
              (value_declaration
                functionDeclarationLeft: (function_declaration_left) @function.params
                body: (_) @function.body) @function.def
                
              ; Type annotations for functions
              (type_annotation
                name: (lower_case_identifier) @function.name
                typeExpression: (type_expression) @function.type) @function.type_def
                
              ; Anonymous functions
              (anonymous_function_expr
                param: (pattern) @function.params
                expr: (_) @function.body) @function.anon
                
              ; Let bindings that define functions
              (let_in_expr
                valueDeclaration: (value_declaration
                  functionDeclarationLeft: (function_declaration_left) @function.params
                  body: (_) @function.body) @function.let_def)
            ] @function
        """
    },
    "gdscript": {
        "function": """
            [
              ; Regular function definitions
              (function_definition
                name: (name) @function.name
                parameters: (parameters)? @function.params
                return_type: (type)? @function.return_type
                body: (body) @function.body) @function.def
                
              ; Static function definitions
              (function_definition
                (static_keyword) @function.static
                name: (name) @function.name
                parameters: (parameters)? @function.params
                return_type: (type)? @function.return_type
                body: (body) @function.body) @function.def
                
              ; Signal callback functions (_on_*)
              (function_definition
                name: (name) @function.name
                (#match? @function.name "^_on_.*")
                parameters: (parameters)? @function.params
                return_type: (type)? @function.return_type
                body: (body) @function.body) @function.def
                
              ; Virtual functions (_ready, _process, etc)
              (function_definition
                name: (name) @function.name
                (#match? @function.name "^_.*")
                parameters: (parameters)? @function.params
                return_type: (type)? @function.return_type
                body: (body) @function.body) @function.def
            ] @function
        """
    },
    "squirrel": {
        "function": """
            [
              ; Regular function declarations
              (function_declaration
                (identifier) @function.name
                (parameters)? @function.params
                (block) @function.body) @function.def
                
              ; Anonymous functions
              (primary_expression
                (anonymous_function
                  (parameters)? @function.params
                  (block) @function.body)) @function.def
                
              ; Function expressions in assignments
              (assignment_expression
                left: (identifier) @function.name
                right: (primary_expression
                  (anonymous_function
                    (parameters)? @function.params
                    (block) @function.body))) @function.def
                
              ; Function expressions in table slots
              (table_slot
                (identifier) @function.name
                (anonymous_function
                  (parameters)? @function.params
                  (block) @function.body)) @function.def
            ] @function
        """
    },
    "php": {
        "function": """
            [
              (function_definition
                name: (_) @function.name
                parameters: (formal_parameters)? @function.params
                body: (compound_statement) @function.body)
              (method_declaration
                name: (_) @function.name
                parameters: (formal_parameters)? @function.params
                body: (compound_statement) @function.body)
              (anonymous_function
                parameters: (formal_parameters)? @function.params
                body: (compound_statement) @function.body)
            ] @function
        """
    },
    "html": {
        "element": '''
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

              ; Script elements
              (script_element
                (start_tag
                  (tag_name) @script.name
                  (attribute
                    (attribute_name) @script.attr.name
                    [
                      (attribute_value) @script.attr.value
                      (quoted_attribute_value
                        (attribute_value) @script.attr.value)
                    ]?)* @script.attrs)
                (raw_text) @script.content
                (end_tag)?) @script.def

              ; Style elements
              (style_element
                (start_tag
                  (tag_name) @style.name
                  (attribute
                    (attribute_name) @style.attr.name
                    [
                      (attribute_value) @style.attr.value
                      (quoted_attribute_value
                        (attribute_value) @style.attr.value)
                    ]?)* @style.attrs)
                (raw_text) @style.content
                (end_tag)?) @style.def
            ] @element.any
        ''',
        "document": '''
            (document
              (doctype)? @document.doctype
              (_)* @document.content) @document
        ''',
        "comment": '''
            (comment) @comment
        '''
    },
    "powershell": {
        "function": '''
            [
              ; Regular function declarations
              (function_statement
                (function_name) @function.name
                (script_block) @function.body) @function
            ]
        '''
    },
    "fish": {
        "function": """
            (function_definition) @function
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
def get_language_patterns(language: str) -> Dict[str, str]:
    """Get all patterns for a language, including common patterns.
    
    Args:
        language: Language identifier
        
    Returns:
        Dictionary of pattern type to pattern string
    """
    # Get base patterns for language
    patterns = QUERY_PATTERNS.get(language, {}).copy()
    
    # Add common patterns only if not already defined
    for pattern_type, pattern in COMMON_PATTERNS.items():
        if pattern_type not in patterns:
            patterns[pattern_type] = pattern
            
    return patterns

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

# Helper function to get language for a file
def get_language_for_file(filename: str) -> Optional[str]:
    """Get the language for a file based on its name or extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        Language identifier or None if not found
    """
    # First check if there's a custom parser
    if get_custom_parser(filename):
        # Let the FileService._detect_language handle custom parser language mapping
        return None
        
    # Then check special filenames
    if filename in SPECIAL_FILENAMES:
        return SPECIAL_FILENAMES[filename]
        
    # Finally check extensions
    ext = filename.split('.')[-1].lower() if '.' in filename else filename.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)

# Update get_query_pattern to use get_language_patterns
def get_query_pattern(language: str, pattern_type: str) -> Optional[str]:
    """Get query pattern for language and type.
    
    Args:
        language: Language identifier
        pattern_type: Type of pattern to get
        
    Returns:
        Query pattern string or None if not found
    """
    # Skip pattern lookup for custom parser languages
    if language in {'requirements', 'env', 'gitignore', 'editorconfig', 'lockfile'}:
        return None
        
    # First try to get the actual language if this is a filename
    if '.' in language or language in SPECIAL_FILENAMES:
        detected_lang = get_language_for_file(language)
        if detected_lang:
            language = detected_lang
        
    # Get all patterns for the language
    patterns = get_language_patterns(language)
    if pattern_type in patterns:
        return patterns[pattern_type]
        
    # Try base language if not found
    base_lang = get_base_language(language)
    if base_lang != language:
        patterns = get_language_patterns(base_lang)
        return patterns.get(pattern_type)

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
    if language in {'jsx', 'tsx', 'javascript', 'typescript'}:
        return 'javascript'  # All JS variants use the same base patterns
    elif language in {'hpp', 'cc', 'hh'}:
        return 'cpp'
    return language 