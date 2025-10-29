"""Configure pytest to find the src package."""

from pathlib import Path
import sys

# Get the absolute path to the project root directory
project_root = Path(__file__).parent.parent.absolute()

# Add the src directory to Python's import path
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# This ensures imports from 'src' work correctly in test files
