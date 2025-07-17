#!/usr/bin/env python3
"""
Notification management for user interaction
"""

import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..database.session_operations import (get_pending_sessions,
                                   update_session_classification)


class NotificationManager:
    """Handles user notifications for activity classification"""

    def __init__(self):
        self.pending_sessions = {}  # Track sessions awaiting user response

    def send_macos_notification(
        self, title: str, message: str, sound: bool = True
    ) -> bool:
        """Send native macOS notification"""
        try:
            cmd = [
                "osascript",
                "-e",
                f'display notification "{message}" with title "{title}"',
            ]
            if sound:
                cmd[-1] += ' sound name "Glass"'

            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"[NOTIFICATION] Failed to send notification: {e}")
            return False

    def prompt_user_for_classification(
        self, session_id: int, session_name: str, duration_min: int, confidence: int
    ) -> Optional[Dict]:
        """Prompt user to classify a session using AppleScript dialog"""

        # Create AppleScript dialog with scale input
        script = f"""
        tell application "System Events"
            set response to display dialog "Rate the productivity of this session:

Session: {session_name}
Duration: {duration_min} minutes
AI Confidence: {confidence}%

Rating Scale:
-50: Very unproductive (major distraction)
-25: Somewhat unproductive (minor distraction)
  0: Neutral (necessary but not advancing goals)
+25: Somewhat productive (helpful for goals)
+50: Very productive (major progress on goals)

Enter score (-50 to +50):" default answer "0" buttons {{"Submit", "Skip"}} default button "Submit" with title "Activity Classification"
            set button_pressed to button returned of response
            set score_text to text returned of response
        end tell
        
        return button_pressed & "|" & score_text
        """

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=60,  # Longer timeout for user input
            )

            if result.returncode == 0:
                response = result.stdout.strip()

                if "|" in response:
                    button, score_text = response.split("|", 1)

                    if button == "Skip":
                        return None

                    try:
                        score = int(score_text)
                        if -50 <= score <= 50:
                            # Convert score to classification and intensity
                            classification, intensity = self._score_to_classification(
                                score
                            )

                            return {
                                "session_id": session_id,
                                "classification": classification,
                                "productivity_score": score,
                                "intensity": intensity,
                                "user_confirmed": True,
                            }
                        else:
                            print(f"[NOTIFICATION] Invalid score range: {score}")
                    except ValueError:
                        print(f"[NOTIFICATION] Invalid score format: {score_text}")

        except subprocess.TimeoutExpired:
            print(f"[NOTIFICATION] User dialog timed out for session {session_id}")
        except Exception as e:
            print(f"[NOTIFICATION] Error showing dialog: {e}")

        return None

    def _score_to_classification(self, score: int):
        """Convert productivity score to classification and intensity"""
        if score >= 25:
            return "productive", "high"
        elif score > 0:
            return "productive", "low"
        elif score == 0:
            return "neutral", "neutral"
        elif score > -25:
            return "unproductive", "low"
        else:
            return "unproductive", "high"

    def check_and_prompt_pending_sessions(self):
        """Check for and prompt user about pending sessions"""
        pending = get_pending_sessions()

        if not pending:
            print("[NOTIFICATION] No pending classifications")
            return

        print(f"[NOTIFICATION] Found {len(pending)} sessions needing classification")

        for session_obj in pending:
            print(f"[NOTIFICATION] Prompting for session: {session_obj.session_name}")

            # Send notification first
            duration_min = session_obj.total_duration_sec // 60
            self.send_macos_notification(
                "Activity Classification Needed",
                f"Session: {session_obj.session_name} ({duration_min}min)",
            )

            # Then show interactive dialog
            result = self.prompt_user_for_classification(
                session_obj.id,
                session_obj.session_name,
                duration_min,
                session_obj.confidence_score,
            )

            if result:
                update_session_classification(
                    result["session_id"],
                    result["classification"],
                    result["user_confirmed"],
                )
                print(f"[NOTIFICATION] User classified as: {result['classification']}")
            else:
                print(f"[NOTIFICATION] User skipped classification")


def run_notification_check():
    """Main function to check and handle pending notifications"""
    notification_manager = NotificationManager()
    notification_manager.check_and_prompt_pending_sessions()


if __name__ == "__main__":
    run_notification_check()
