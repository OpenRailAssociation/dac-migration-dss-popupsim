"""Configure pytest to find the src package."""

from pathlib import Path
import sys

# Get the absolute path to the project root directory
project_root = Path(__file__).parent.parent.absolute()

# Add the project root to Python's import path
sys.path.insert(0, str(project_root))

# This ensures imports from 'src' work correctly in test files
