"""Build tree-sitter language files"""
from tree_sitter import Language
from pathlib import Path

def build_languages():
    """Build tree-sitter language files"""
    build_dir = Path(__file__).parent.parent / "src" / "GithubAnalyzer" / "core" / "parsers" / "build"
    build_dir.mkdir(exist_ok=True)
    
    Language.build_library(
        str(build_dir / "languages.so"),
        [
            'vendor/tree-sitter-python'
        ]
    )

if __name__ == "__main__":
    build_languages() 