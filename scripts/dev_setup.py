"""Development environment setup."""

import subprocess
from pathlib import Path

def setup_dev_environment():
    """Set up development environment."""
    # Install dependencies
    subprocess.run(["pip", "install", "-r", "requirements/test.txt"], check=True)
    
    # Build language support
    from scripts.build_languages import build_languages
    build_languages()
    
    # Run basic tests
    subprocess.run(["pytest", "tests/unit/test_parser_initialization.py", "-v"], check=True)


if __name__ == "__main__":
    setup_dev_environment() 