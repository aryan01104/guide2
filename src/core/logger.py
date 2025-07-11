#!/usr/bin/env python3
""" Activity logging core module: polls every POLL_SEC seconds and logs each interval to the database. """

import datetime as dt
import threading
import time
from typing import Tuple

from ..analysis.realtime_session_grouper import RealTimeSessionGrouper
from ..database.operations import add_activity_log, init_database, update_activity_scores

POLL_SEC: int = 10  # Poll interval in seconds


def _get_active() -> Tuple[str, str]:
    """
    Returns (event, details)
      event   = "app_session" or "browser_tab_session"
      details = window title OR "<tab title>|<url>"
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
        from subprocess import check_output

        script = (
            'tell application "Google Chrome"\n'
            '  if not (exists window 1) then return "Unknown||Unknown"\n'
            '  set t to title of active tab of front window\n'
            '  set u to URL of active tab of front window\n'
            '  return t & "||" & u\n'
            'end tell'
        )
        try:
            out = check_output(["osascript", "-e", script])
            tab_title, url = out.decode().strip().split("||", 1)
            return ("browser_tab_session", f"{tab_title}|{url}")
        except Exception:
            return ("browser_tab_session", "Unknown|Unknown")

    return ("app_session", title)


def start_logging():
    """Start activity logging in a background thread."""

    def _thread():
        print("[LOGGER] Logger thread started!")
        try:
            # Initialize database
            init_database()
            print("[LOGGER] Database initialized.")

            # Initialize real-time session grouper
            session_grouper = RealTimeSessionGrouper()
            print("[LOGGER] Session grouper initialized.")

            # Seed previous state
            prev_event, prev_details = _get_active()
            start_ts = time.time()

            while True:
                time.sleep(POLL_SEC)

                # Always log every POLL_SEC interval
                cur_event, cur_details = _get_active()
                duration = int(time.time() - start_ts)
                timestamp = dt.datetime.now()

                # Log to database
                activity = add_activity_log(
                    timestamp_start=timestamp,
                    event_type=cur_event,
                    details=cur_details,
                    duration_sec=duration,
                )

                print(
                    f"[LOGGER] Logged: event={cur_event}, details={cur_details}, duration={duration}s"
                )

                # Process with real-time session grouper
                if activity:
                    try:
                        session_grouper.on_new_activity(activity)

                        # Update DB with classification scores if set
                        if (
                            hasattr(activity, "productivity_score")
                            and activity.productivity_score is not None
                        ):
                            update_activity_scores(
                                activity.id,
                                activity.productivity_score,
                                getattr(activity, "confidence_score", None),
                                getattr(activity, "classification_text", None),
                            )
                    except Exception as e:
                        print(f"[LOGGER] Error in session grouper: {e}")

                # Reset for next interval
                prev_event, prev_details = cur_event, cur_details
                start_ts = time.time()
        except Exception as e:
            print(f"[LOGGER] Exception in logger thread: {e}")

    thread = threading.Thread(target=_thread, daemon=True)
    thread.start()
    return thread
