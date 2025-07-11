#!/usr/bin/env python3
"""
Main entry point for the activity tracker application
"""

import threading
import time
from datetime import datetime

from .core.logger import start_logging
from .core.scheduler import start as start_basic_scheduler
from .database.operations import init_database
from .notifications.manager import NotificationManager
# Import user config from same directory
from .user_config import setup_user_config


class SmartScheduler:
    """Handles periodic analysis and user prompts for activity classification"""

    def __init__(self, analysis_interval_minutes: int = 30):
        self.analysis_interval = analysis_interval_minutes * 60  # Convert to seconds
        self.notification_manager = NotificationManager()
        self.running = False

    def run_analysis_cycle(self):
        """Run one cycle of pending-session prompts"""
        print(f"[SMART_SCHEDULER] Checking at {datetime.now().strftime('%H:%M:%S')}")
        try:
            self.notification_manager.check_and_prompt_pending_sessions()
        except Exception as e:
            print(f"[SMART_SCHEDULER] Error during classification check: {e}")


    def start_scheduler(self):
        """Start the smart scheduler in a background thread"""

        def scheduler_thread():
            print(
                f"[SMART_SCHEDULER] Starting smart scheduler (every {self.analysis_interval//60} minutes)"
            )
            self.running = True

            # Run initial analysis after 60 seconds
            time.sleep(60)
            if self.running:
                self.run_analysis_cycle()

            while self.running:
                time.sleep(self.analysis_interval)
                if self.running:  # Check again in case we were stopped during sleep
                    self.run_analysis_cycle()

        thread = threading.Thread(target=scheduler_thread, daemon=True)
        thread.start()
        return thread

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        print("[SMART_SCHEDULER] Scheduler stopped")


def main():
    """Main application entry point"""
    import sys

    # Check if user wants web server too
    start_web = "--with-web" in sys.argv or "-w" in sys.argv

    # Initialize database
    init_database()
    # Setup user configuration
    setup_user_config()

    # Start activity logging
    logger_thread = start_logging()
    print("[MAIN] logging activities to db")

    # Start basic scheduler (for legacy compatibility)
    start_basic_scheduler()
    print("[MAIN] ✅ Basic scheduler started")

    # Note: Real-time session grouping is now handled in the logger thread
    print("[MAIN] ✅ Real-time session grouping enabled")

    # Optionally start web server
    if start_web:
        from .web.app import app

        web_thread = threading.Thread(
            target=lambda: app.run(host="0.0.0.0", port=5001, debug=False), daemon=True
        )
        web_thread.start()
        print("[MAIN] ✅ Web server started at http://localhost:5001")

    print("\n🚀 System is now running!")
    print("Features:")
    print("  • Automatic activity tracking")
    print("  • Real-time session grouping (context-switch aware)")
    print("  • Flow-aware classification with natural breakpoints")
    print("  • Pattern learning and recognition")
    print("  • Sessions created based on work/break transitions")
    if start_web:
        print("  • Web interface at http://localhost:5001")
    else:
        print("  • Web interface: run 'python scripts/run_web_server.py'")
    print("\nPress Ctrl+C to exit")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down...")
        print("[MAIN] ✅ Clean shutdown complete")


if __name__ == "__main__":
    main()
