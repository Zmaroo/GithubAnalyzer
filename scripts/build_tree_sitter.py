"""Script to build tree-sitter language libraries."""

import os
import subprocess
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, shell=True, check=True, capture_output=True, text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error output: {e.stderr}")
        raise


def clone_and_build_grammar(language, repo_url):
    """Clone and build a tree-sitter grammar."""
    build_dir = Path("build") / f"tree-sitter-{language}"

    # Clone repository if it doesn't exist
    if not build_dir.exists():
        print(f"Cloning {language} grammar...")
        run_command(f"git clone {repo_url} {build_dir}")

    # Build the grammar
    print(f"Building {language} grammar...")
    run_command("git pull", cwd=build_dir)  # Update to latest
    run_command("make", cwd=build_dir)

    return build_dir


def main():
    """Main function to build all grammars."""
    # Create build directory
    build_root = Path("build")
    build_root.mkdir(exist_ok=True)

    # Define language repositories
    languages = {
        "python": "https://github.com/tree-sitter/tree-sitter-python",
        "javascript": "https://github.com/tree-sitter/tree-sitter-javascript",
        "typescript": "https://github.com/tree-sitter/tree-sitter-typescript",
        "java": "https://github.com/tree-sitter/tree-sitter-java",
        "cpp": "https://github.com/tree-sitter/tree-sitter-cpp",
        "rust": "https://github.com/tree-sitter/tree-sitter-rust",
        "go": "https://github.com/tree-sitter/tree-sitter-go",
        "ruby": "https://github.com/tree-sitter/tree-sitter-ruby",
    }

    # Build each grammar
    for language, repo in languages.items():
        try:
            build_dir = clone_and_build_grammar(language, repo)
            print(f"Successfully built {language} grammar")
        except Exception as e:
            print(f"Failed to build {language} grammar: {e}")

    print("\nDone building grammars!")
    print("\nTo use these grammars with tree-sitter-python:")
    print("1. Install the tree-sitter Python package: pip install tree-sitter")
    print(
        "2. In your code, use Language.build_library() to generate the shared library"
    )
    print("3. Point your parser to the generated library file")


if __name__ == "__main__":
    main()
