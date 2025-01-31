from tree_sitter_language_pack import get_binding, get_language, get_parser
import os

# Read the TypeScript file
ts_file_path = os.path.join(os.path.dirname(__file__), 'types.ts')
with open(ts_file_path, 'rb') as f:
    code = f.read()

# Using tree-sitter-language-pack
ts_lang = get_language('typescript')
parser = get_parser('typescript')

# Parse the code
tree = parser.parse(code)

# Define the query
query = ts_lang.query("""
[
  (function_declaration)
  (function_expression)
  (arrow_function)
  (method_definition)
] @function
""")

# Execute the query
matches = query.matches(tree.root_node)

# Process the matches to get function details
function_count = 0
functions_info = []

for pattern_index, capture_dict in matches:
    for capture_name, nodes in capture_dict.items():
        for node in nodes:
            function_count += 1

            # Extract function name (if available)
            function_name = "Anonymous"
            if node.type == "function_declaration":
                # Function declarations have a name
                name_node = node.child_by_field_name("name")
                if name_node:
                    function_name = code[name_node.start_byte:name_node.end_byte]
            
            elif node.type == "method_definition":
                # Methods have a name
                name_node = node.child_by_field_name("name")
                if name_node:
                    function_name = code[name_node.start_byte:name_node.end_byte]

            functions_info.append({
                "name": function_name,
                "type": node.type,
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "code": code[node.start_byte:node.end_byte],
            })

# Output the function count and details
print(f"Total functions found: {function_count}")
for func in functions_info:
    print(f"\nFunction Name: {func['name']}")
    print(f"Type: {func['type']}")
    print(f"Code:\n{func['code']}")