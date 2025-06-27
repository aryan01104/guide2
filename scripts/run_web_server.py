#!/usr/bin/env python3
"""
Standalone script to run the web server
"""

import sys
import pathlib

# Add project root to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.web.app import run_web_app

if __name__ == "__main__":
    run_web_app()