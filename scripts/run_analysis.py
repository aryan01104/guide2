#!/usr/bin/env python3
"""
Standalone script to run pattern analysis
"""

import sys
import pathlib

# Add project root to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.analysis.pattern_recognition import analyze_and_group_activities
from src.database.operations import init_database

if __name__ == "__main__":
    init_database()
    results = analyze_and_group_activities()
    
    print(f"\nAnalysis Results:")
    print(f"Found {len(results)} sessions")
    
    for result in results:
        status = "✅ AUTO" if result['auto_classified'] else "⚠️  NEEDS REVIEW"
        duration_min = sum(a.duration_sec for a in result['activities']) // 60
        print(f"  • {result['session_name']} ({duration_min}min, {result['confidence']}%) [{status}]")