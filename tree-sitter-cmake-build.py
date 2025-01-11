from tree_sitter import Language

# Build the language library
Language.build_library(
    'build/my-languages.so',  # Path to the output shared library
    [
        './tree-sitter-cmake',  # Replace with the actual path to the cloned repository
        # Add paths to other language parsers if needed
    ]
)