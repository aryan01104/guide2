#!/usr/bin/env python3
""" Activity polling core module: polls every POLL_SEC seconds and logs each interval to the database. """

print("Starting poller script...")

import datetime as dt
import time
from typing import Tuple
from dotenv import load_dotenv
load_dotenv()
import os

from supabase import create_client

POLL_SEC = 10  # seconds


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
    except Exception as e:
        print(f"[DEBUG] Error getting active window: {e}")
        return ("app_session", "Unknown")

    if "Chrome" in title:
        from subprocess import check_output

        script = """
tell application "Google Chrome"
  if not (exists window 1) then return "Unknown||Unknown"
  set t to title of active tab of front window
  set u to URL of active tab of front window
  return t & "||Google Chrome||" & u
end tell
"""
        try:
            out = check_output(["osascript", "-e", script])
            tab_title, app_name, url = out.decode().strip().split("||", 2)
            return ("browser_tab_session", f"{tab_title} | {app_name} | {url}")
        except Exception as e:
            print(f"[DEBUG] Error getting Chrome tab details: {e}")
            return ("browser_tab_session", "Unknown|Unknown")

    return ("app_session", title)


def poll_loop(supabase):
    print("[POLLER] POLLER loop started!")
    prev_details = None
    start_ts = time.time()

    try:
        while True:
            time.sleep(POLL_SEC)

            _, cur_details = _get_active()
            duration = int(time.time() - start_ts)
            timestamp = dt.datetime.now()

            if cur_details != prev_details:
                try:
                    response = supabase.table("activity_logs").insert({
                        "timestamp_start": timestamp.isoformat(),
                        "details": cur_details,
                        "duration_sec": duration,
                        "productivity_score": 0,
                        "user_provided": False,
                        "session_id": None,
                    }).execute()

                    if response.data is None or response.data == []:
                        print(f"[POLLER] Failed to insert activity log: no data returned")
                    else:
                        print(f"[POLLER] Logged activity: {cur_details}, duration {duration}s")
                except Exception as e:
                    print(f"[POLLER] Error inserting activity log: {e}")

                prev_details = cur_details
                start_ts = time.time()
    except Exception as e:
        print(f"[POLLER] Unhandled error in poll_loop: {e}")


def main():
    print("[MAIN] Starting main function...")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print(f"[ERROR] SUPABASE_URL or SUPABASE_KEY environment variable missing. URL: {url}, Key: {key}")
        return

    supabase = create_client(url, key)
    print("[MAIN] Supabase client created.")

    poll_loop(supabase)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MAIN] Polling stopped by user.")
