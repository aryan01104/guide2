#!/usr/bin/env python3
"""
Config module exports
"""

import os
import pathlib

# Project root
ROOT = pathlib.Path(__file__).parent.parent

# OpenAI settings
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Export all settings
from .settings import *
