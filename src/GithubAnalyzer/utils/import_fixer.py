from typing import List, Set, Dict, Pattern, Optional, Tuple, Callable
import logging
import re
"""Utility to fix imports across the project."""
import os
from pathlib import Path
from GithubAnalyzer.utils.logging.logging_config import get_logger

logger = get_logger(__name__)

class ImportFixer:
    """Fixes imports in Python files."""
    
    def __init__(self):
        """Initialize the import fixer with patterns."""
        self.patterns: List[Tuple[str, Callable[[re.Match], str]]] = [
            # PDM src layout patterns
            (r'from\s+src\.GithubAnalyzer\.([\w\.]+)\s+import', lambda m: f'from GithubAnalyzer.{m.group(1)} import'),
            (r'from\s+src\.([\w\.]+)\s+import', lambda m: f'from GithubAnalyzer.{m.group(1)} import'),
            (r'import\s+src\.GithubAnalyzer(?:\s|$)', lambda m: 'import GithubAnalyzer'),
            
            # Database services and config
            (r'from\s+GithubAnalyzer\.services\.database\.([\w\.]+)\s+import', 
             lambda m: f'from GithubAnalyzer.services.core.database.{m.group(1)} import'),
            (r'from\s+GithubAnalyzer\.database\.([\w\.]+)\s+import',
             lambda m: f'from GithubAnalyzer.services.core.database.{m.group(1)} import'),
            (r'from\s+GithubAnalyzer\.config\.db_config\s+import',
             lambda m: 'from GithubAnalyzer.services.core.database.db_config import'),
            (r'from\s+GithubAnalyzer\.embedding_service\s+import',
             lambda m: 'from GithubAnalyzer.services.core.database.embedding_service import'),
            
            # Logging structure
            (r'from\s+GithubAnalyzer\.config\.logging_config\s+import',
             lambda m: 'from GithubAnalyzer.utils.logging.logging_config import'),
            (r'from\s+GithubAnalyzer\.utils\.logging_config\s+import', 
             lambda m: 'from GithubAnalyzer.utils.logging.logging_config import'),
            (r'from\s+GithubAnalyzer\.utils\.formatters\s+import',
             lambda m: 'from GithubAnalyzer.utils.logging.formatters import'),
            (r'from\s+GithubAnalyzer\.services\.analysis\.parsers\.tree_sitter_logging\s+import',
             lambda m: 'from GithubAnalyzer.utils.logging.tree_sitter_logging import'),
            
            # Core/Analysis structure
            (r'from\s+GithubAnalyzer\.core\.models\.([\w\.]+)\s+import', 
             lambda m: f'from GithubAnalyzer.models.core.{m.group(1)} import'),
            (r'from\s+GithubAnalyzer\.analysis\.models\.([\w\.]+)\s+import',
             lambda m: f'from GithubAnalyzer.models.analysis.{m.group(1)} import'),
            (r'from\s+GithubAnalyzer\.core\.services\.([\w\.]+)\s+import',
             lambda m: f'from GithubAnalyzer.services.core.{m.group(1)} import'),
            (r'from\s+GithubAnalyzer\.analysis\.services\.([\w\.]+)\s+import',
             lambda m: f'from GithubAnalyzer.services.analysis.{m.group(1)} import'),
            (r'from\s+GithubAnalyzer\.core\.([\w\.]+)\s+import',
             lambda m: f'from GithubAnalyzer.{m.group(1)} import'),
            
            # Test imports
            (r'from\s+tests\.core\.([\w\.]+)\s+import',
             lambda m: f'from tests.models.core.{m.group(1)} import'),
            (r'from\s+tests\.analysis\.([\w\.]+)\s+import',
             lambda m: f'from tests.models.analysis.{m.group(1)} import'),
            (r'from\s+tests\.services\.([\w\.]+)\s+import',
             lambda m: f'from tests.services.{m.group(1)} import'),
            
            # Handle old utils structure
            (r'from\s+GithubAnalyzer\.core\.utils\.([\w\.]+)\s+import',
             lambda m: f'from GithubAnalyzer.utils.{m.group(1)} import'),
            (r'from\s+GithubAnalyzer\.utils\.log_utils\s+import',
             lambda m: 'from GithubAnalyzer.utils.logging.logging_config import'),
            
            # Remove settings imports since they're unused
            (r'from\s+GithubAnalyzer\.config\.settings\s+import\s+[\w\s,]+\n', lambda m: ''),
            (r'from\s+GithubAnalyzer\.config\s+import\s+settings\n', lambda m: ''),
            
            # Error handling patterns
            (r'from\s+GithubAnalyzer\.core\.models\.errors\s+import',
             lambda m: 'from GithubAnalyzer.models.core.errors import'),
        ]
    
    def fix_imports(self, content: str) -> str:
        """Fix imports in the given content."""
        for pattern, replacement in self.patterns:
            content = re.sub(pattern, replacement, content)
        return content
    
    def fix_file(self, file_path: str) -> None:
        """Fix imports in a file."""
        details = {
            "file_path": file_path,
            "patterns_count": len(self.patterns)
        }
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            fixed_content = self.fix_imports(content)
            if fixed_content != content:
                logger.info({
                    "message": f"Fixing imports in {file_path}",
                    "context": details
                })
                with open(file_path, 'w') as f:
                    f.write(fixed_content)
        except Exception as e:
            error_details = {**details, "error": str(e)}
            logger.error({
                "message": f"Error fixing imports in {file_path}",
                "context": error_details
            })
            raise
    
    def fix_directory(self, directory: str) -> None:
        """Fix imports in all Python files in a directory."""
        details = {"directory": directory}
        
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py'):
                        self.fix_file(os.path.join(root, file))
        except Exception as e:
            error_details = {**details, "error": str(e)}
            logger.error({
                "message": f"Error fixing imports in directory {directory}",
                "context": error_details
            })
            raise
    
    def fix_project(self, project_root: str) -> None:
        """Fix imports in all Python files in the project."""
        details = {"project_root": project_root}
        
        try:
            src_dir = os.path.join(project_root, 'src')
            tests_dir = os.path.join(project_root, 'tests')
            
            if os.path.exists(src_dir):
                logger.info({
                    "message": f"Fixing imports in {src_dir}",
                    "context": {"directory": src_dir}
                })
                self.fix_directory(src_dir)
                
            if os.path.exists(tests_dir):
                logger.info({
                    "message": f"Fixing imports in {tests_dir}",
                    "context": {"directory": tests_dir}
                })
                self.fix_directory(tests_dir)
        except Exception as e:
            error_details = {**details, "error": str(e)}
            logger.error({
                "message": "Error fixing project imports",
                "context": error_details
            })
            raise

def fix_project_imports() -> None:
    """Fix imports across the entire project."""
    try:
        fixer = ImportFixer()
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        logger.info({
            "message": "Starting import fixes",
            "context": {"project_root": project_root}
        })
        fixer.fix_project(project_root)
    except Exception as e:
        logger.error({
            "message": "Error fixing imports",
            "context": {"error": str(e)}
        })
        raise

if __name__ == "__main__":
    fix_project_imports() 