"""Global pytest test configuration and fixtures."""

import os
import sys
from pathlib import Path
import pytest

# Add python-engine root to python path for testing
engine_root = Path(__file__).parent.parent
sys.path.insert(0, str(engine_root))
