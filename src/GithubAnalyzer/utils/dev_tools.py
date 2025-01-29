"""Development tools for GithubAnalyzer project."""
import sys
import os
import argparse
from pathlib import Path
import importlib.util
from typing import Optional

from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

def fix_imports_bootstrap():
    """Bootstrap function to fix imports without requiring package imports."""
    try:
        # Get absolute path to project root and source
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        src_path = project_root / "src"
        
        # Add project root to Python path if not already there
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            
        # Add src to Python path if not already there
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            
        # Import the import fixer module using importlib
        import_fixer_path = src_path / "GithubAnalyzer/utils/import_fixer.py"
        spec = importlib.util.spec_from_file_location("import_fixer", import_fixer_path)
        import_fixer = importlib.util.module_from_spec(spec)
        sys.modules["import_fixer"] = import_fixer
        spec.loader.exec_module(import_fixer)
        
        # Run the import fixer
        fixer = import_fixer.ImportFixer()
        fixer.fix_project(project_root)
        return True
    except Exception as e:
        logger.error(f"Error fixing imports: {str(e)}")
        return False

def main():
    """Main entry point for development tools."""
    parser = argparse.ArgumentParser(description="GithubAnalyzer Development Tools")
    parser.add_argument('command', choices=['fix-imports'], help='Development command to run')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'fix-imports':
            success = fix_imports_bootstrap()
            if not success:
                sys.exit(1)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 