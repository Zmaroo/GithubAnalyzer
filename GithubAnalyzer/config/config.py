import os
from dotenv import load_dotenv
from ..core.utils.logging import setup_logger

logger = setup_logger(__name__)

# Load environment variables
load_dotenv()

# Database connection strings
PG_CONN_STRING = os.getenv('PG_CONN_STRING', 'postgres://postgres:postgres@localhost:5432/code_analysis')
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')

# Language mapping for Tree-sitter
LANGUAGE_MAP = {
    # Programming Languages
    '.py': 'python',
    'setup.py': 'pymanifest',
    'pyproject.toml': 'pymanifest',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cs': 'c-sharp',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.scala': 'scala',
    '.kt': 'kotlin',
    '.lua': 'lua',
    '.cu': 'cuda',
    '.ino': 'arduino',
    '.pde': 'arduino',
    '.m': 'matlab',
    '.groovy': 'groovy',
    'build.gradle': 'groovy',
    
    # Build Systems
    'CMakeLists.txt': 'cmake',
    '.cmake': 'cmake',
    
    # Web Technologies
    '.html': 'html',
    '.css': 'css',
    
    # Data & Config
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.xml': 'xml',
    
    # Query Languages
    '.sql': 'sql',
    
    # Documentation
    '.md': 'markdown',
    '.markdown': 'markdown',
    
    # Shell Scripts
    '.sh': 'bash',
    '.bash': 'bash',
    '.env': 'bash'
}
