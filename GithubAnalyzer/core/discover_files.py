import os
import json
from pygments import lex
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound
import chardet  # For detecting file encoding
import sys
from .utils import setup_logger

logger = setup_logger(__name__)

def discover_files(repo_path):
    files = []
    for root, _, filenames in os.walk(repo_path):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "rb") as f:  # Open as bytes to detect encoding
                    rawdata = f.read()
                    encoding = chardet.detect(rawdata)['encoding']
                with open(filepath, "r", encoding=encoding) as f:
                    content = f.read()
                    try:
                        lexer = guess_lexer(content)  # Try to guess lexer
                        language = lexer.name
                    except ClassNotFound:
                        language = "unknown"
                    files.append({"path": filepath, "content": content, "language": language})
            except Exception as e:
                print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return {"files": files}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"status": "error", "message": "Usage: python discover_files.py <repo_path>", "files": []}))
        sys.exit(1)
    repo_path = sys.argv[1]
    result = discover_files(repo_path)
    print(json.dumps(result))