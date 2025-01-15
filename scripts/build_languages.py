"""Build tree-sitter language support."""

import os
import subprocess
from pathlib import Path

from tree_sitter import Language

# Define language repositories
LANGUAGES = {
    "python": "https://github.com/tree-sitter/tree-sitter-python",
    "javascript": "https://github.com/tree-sitter/tree-sitter-javascript",
    # Add other languages as needed
}

def build_languages():
    """Build tree-sitter language support."""
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)
    
    languages_dir = Path("languages")
    languages_dir.mkdir(exist_ok=True)
    
    for lang, repo in LANGUAGES.items():
        lang_dir = languages_dir / f"tree-sitter-{lang}"
        
        # Clone repository if not exists
        if not lang_dir.exists():
            subprocess.run(
                ["git", "clone", repo, str(lang_dir)],
                check=True
            )
        
        # Build language
        try:
            Language.build_library(
                # Store .so files in build dir
                str(build_dir / f"{lang}.so"),
                # Include language source
                [str(lang_dir)]
            )
            print(f"Successfully built {lang} parser")
        except Exception as e:
            print(f"Failed to build {lang} parser: {e}")


if __name__ == "__main__":
    build_languages() 