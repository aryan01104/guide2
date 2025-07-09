#!/usr/bin/env python3
"""
Decision engine for real-time session management
"""

from datetime import datetime, timedelta
from typing import List

from config.settings import REALTIME_SESSION_SETTINGS

from ..database.models import ActivityLog


class SessionDecisionEngine:
    """Makes decisions about when to create, end, or continue sessions"""

    def __init__(self):
        # Load configuration
        self.minimum_focus_time = REALTIME_SESSION_SETTINGS[
            "minimum_focus_time_seconds"
        ]
        self.minimum_break_time = REALTIME_SESSION_SETTINGS[
            "minimum_break_time_seconds"
        ]
        self.context_switch_threshold = REALTIME_SESSION_SETTINGS[
            "context_switch_threshold_seconds"
        ]
        self.noise_threshold = REALTIME_SESSION_SETTINGS["noise_threshold_seconds"]
        self.session_timeout = REALTIME_SESSION_SETTINGS["session_timeout_seconds"]

    def is_noise_activity(self, activity: ActivityLog) -> bool:
        """Check if activity should be ignored as noise"""
        return activity.duration_sec < self.noise_threshold

    def should_create_session(
        self, current_context: str, time_in_context: float, new_activity_type: str
    ) -> bool:
        """Decide if we should end current session and start new one"""

        if current_context == "productive":
            # End productive session if we've been focused for minimum time
            # and switching to unproductive
            if (
                time_in_context >= self.minimum_focus_time
                and new_activity_type == "unproductive"
            ):
                print(
                    f"[SESSION_DECISION] Productive focus time met ({time_in_context}s >= {self.minimum_focus_time}s), switching to break"
                )
                return True

        elif current_context == "unproductive":
            # End break session if we've been breaking for minimum time
            # and switching to productive
            if (
                time_in_context >= self.minimum_break_time
                and new_activity_type == "productive"
            ):
                print(
                    f"[SESSION_DECISION] Break time met ({time_in_context}s >= {self.minimum_break_time}s), switching to work"
                )
                return True

        # Always end session if context switch is major (5+ minutes)
        if time_in_context >= self.context_switch_threshold:
            print(
                f"[SESSION_DECISION] Context switch threshold met ({time_in_context}s >= {self.context_switch_threshold}s)"
            )
            return True

        return False

    def is_session_timeout(self, last_activity: ActivityLog) -> bool:
        """Check if current session has timed out due to inactivity"""
        if not last_activity:
            return False

        last_activity_end = last_activity.timestamp_start + timedelta(
            seconds=last_activity.duration_sec
        )
        time_since_last = datetime.now() - last_activity_end

        return time_since_last.total_seconds() > self.session_timeout

    def should_add_pending_activities(
        self,
        pending_activities: List[ActivityLog],
        new_activity_type: str,
        classifier_func,
    ) -> List[ActivityLog]:
        """Determine which pending activities match the new session type"""
        matching_pending = [
            a for a in pending_activities if classifier_func(a) == new_activity_type
        ]
        return matching_pending
