"""Utilities for code analysis and preprocessing."""

import re
from typing import List


def preprocess_code(code: str) -> str:
    """Preprocess code for analysis.

    Args:
        code: Raw code string to preprocess

    Returns:
        Preprocessed code string with normalized whitespace and removed comments
    """
    # Remove comments
    code = re.sub(r"#.*$", "", code, flags=re.MULTILINE)  # Python comments
    code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)  # Single line comments
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)  # Multi-line comments

    # Normalize whitespace
    code = re.sub(r"\s+", " ", code)
    code = code.strip()

    return code


def extract_imports(code: str) -> List[str]:
    """Extract import statements from code.

    Args:
        code: Code string to analyze

    Returns:
        List of import statements found in the code
    """
    imports = []
    import_pattern = r"^(?:from\s+[\w.]+\s+)?import\s+[\w.,\s]+$"

    for line in code.split("\n"):
        line = line.strip()
        if re.match(import_pattern, line):
            imports.append(line)

    return imports


def extract_functions(code: str) -> List[str]:
    """Extract function definitions from code.

    Args:
        code: Code string to analyze

    Returns:
        List of function names found in the code
    """
    functions = []
    function_pattern = r"def\s+([a-zA-Z_]\w*)\s*\("

    matches = re.finditer(function_pattern, code)
    for match in matches:
        functions.append(match.group(1))

    return functions
