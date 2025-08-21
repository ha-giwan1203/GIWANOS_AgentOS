"""
VELOS Test Suite
Comprehensive testing infrastructure for VELOS system components.
"""

import os
import sys
from pathlib import Path

# Add VELOS root to path for testing
test_root = Path(__file__).parent.parent
sys.path.insert(0, str(test_root))

__version__ = "1.0.0"
__author__ = "VELOS Development Team"
