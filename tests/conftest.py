"""
Pytest configuration file for the blackjack-agent project.
This file helps configure the Python path for test discovery.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root)) 