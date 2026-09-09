"""
Pytest configuration for Energy-Aware Routing Protocol.
Adds src directory to Python path for testing.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
