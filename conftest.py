import os
import sys
from pathlib import Path

# Get the absolute path of the project root
project_root = Path(__file__).parent

# Add the project root to Python path
sys.path.insert(0, str(project_root)) 