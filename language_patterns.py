# Extended patterns for C# based on csharp-node-types.json
CSHARP_PATTERNS = {
    "function": r"(method_declaration|constructor_declaration|local_function_statement)",
    "import": r"(using_directive)",
    "class": r"(class_declaration)",
    "variable": r"(variable_declaration)",
    "conditional": r"(if_statement|switch_statement|switch_expression)",
    "loop": r"(for_statement|foreach_statement|while_statement|do_statement)",
    "lambda": r"(lambda_expression)"
} 