#!/usr/bin/env python3
"""
Activity logging core module
Tracks window/app changes and logs to database
"""

import datetime as dt
import threading
import time
from typing import Tuple

from ..database.operations import init_database, add_activity_log, update_activity_scores
from ..analysis.realtime_session_grouper import RealTimeSessionGrouper

POLL_SEC: int = 10

def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")

def _get_active() -> Tuple[str, str]:
    """
    Returns (event, details)
      event   = "app_session" or "browser_tab_session"
      details = window title  OR  "<tab title>|<url>"
    """
    try:
        from pygetwindow import getActiveWindow
        win = getActiveWindow()
        if not win:
            return ("app_session", "Unknown")
        title = win.title() if callable(win.title) else win.title
    except Exception:
        return ("app_session", "Unknown")

    if "Chrome" in title:
        tab_title, url = _get_chrome_tab()
        return ("browser_tab_session", f"|{tab_title}|{url}")
    return ("app_session", f"|{title}")

def _get_chrome_tab() -> Tuple[str, str]:
    script = (
        'tell application "Google Chrome"\n'
        '  if not (exists window 1) then return "Unknown||Unknown"\n'
        '  set t to title of active tab of front window\n'
        '  set u to URL of active tab of front window\n'
        '  return t & "||" & u\n'
        'end tell'
    )
    try:
        import subprocess, platform
        if platform.system() != "Darwin":
            raise RuntimeError("Not macOS")
        out = subprocess.check_output(["osascript", "-e", script])
        return out.decode().strip().split("||", 1)
    except Exception:
        return ("Unknown", "Unknown")

def start_logging():
    """Start activity logging in background thread"""
    def _thread():
        print("[LOGGER] Logger thread started!")
        try:
            # Initialize database
            init_database()
            print("[LOGGER] Logger started and running.")
            
            # Initialize real-time session grouper
            session_grouper = RealTimeSessionGrouper()
            print("[LOGGER] Real-time session grouper initialized")
            
            prev_event, prev_details = _get_active()
            start_ts = time.time()

            while True:
                time.sleep(POLL_SEC)
                cur_event, cur_details = _get_active()
                if (cur_event, cur_details) != (prev_event, prev_details):
                    duration = int(time.time() - start_ts)
                    timestamp = dt.datetime.now()
                    
                    # Log to database (initially without scores)
                    activity = add_activity_log(
                        timestamp_start=timestamp,
                        event_type=prev_event,
                        details=prev_details,
                        duration_sec=duration
                    )
                    
                    print(f"[LOGGER] Logged: event={prev_event}, details={prev_details}, duration={duration}s")
                    
                    # Process with real-time session grouper (this will trigger classification and scoring)
                    if activity:
                        try:
                            session_grouper.on_new_activity(activity)
                            
                            # Update activity in database with scores if they were set during classification
                            if hasattr(activity, 'productivity_score') and activity.productivity_score is not None:
                                update_activity_scores(activity.id, activity.productivity_score, 
                                                     getattr(activity, 'confidence_score', None),
                                                     getattr(activity, 'classification_text', None))
                        except Exception as e:
                            print(f"[LOGGER] Error in session grouper: {e}")
                    
                    prev_event, prev_details = cur_event, cur_details
                    start_ts = time.time()
        except Exception as e:
            print(f"[LOGGER] Exception in logger thread: {e}")
    
    th = threading.Thread(target=_thread, daemon=True)
    th.start()
    return th