#!/usr/bin/env python3
"""
Core scheduling functionality - now simplified for basic operations
"""

import time
import threading
from datetime import datetime, timedelta

from ..database.operations import get_recent_activities

def start():
    """Start basic scheduler for legacy compatibility"""
    def scheduler_thread():
        print("[SCHEDULER] Basic scheduler started")
        
        while True:
            time.sleep(300)  # 5 minutes
            
            # Basic health check
            try:
                activities = get_recent_activities(hours_back=1)
                print(f"[SCHEDULER] Health check: {len(activities)} activities in last hour")
            except Exception as e:
                print(f"[SCHEDULER] Health check failed: {e}")
    
    thread = threading.Thread(target=scheduler_thread, daemon=True)
    thread.start()
    return thread