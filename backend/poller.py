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


def poll_loop(supabase):
    print("[POLLER] POLLER loop started!")
    prev_details = None
    start_ts = time.time()

    while True:
        time.sleep(POLL_SEC)

        _, cur_details = _get_active()
        duration = int(time.time() - start_ts)
        timestamp = dt.datetime.now()

        if cur_details != prev_details:
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

            prev_details = cur_details
            start_ts = time.time()


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("[ERROR] SUPABASE_URL or SUPABASE_KEY environment variable missing.")
        return

    supabase = create_client(url, key)

    poll_loop(supabase)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MAIN] Polling stopped by user.")
