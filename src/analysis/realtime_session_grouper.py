#!/usr/bin/env python3
"""
Real-time session grouping based on context switches and natural workflow patterns
"""

from datetime import datetime, timedelta

from src.commentator import generate_transition_commentary
from src.database.operations import add_commentary_to_session
from src.notifications.manager import NotificationManager

from ..database.models import ActivityLog
from .activity_classifier import ActivityClassifier
from .session_persistence import SessionPersistence
from .session_state import SessionState


class RealTimeSessionGrouper:
    """Groups activities into sessions in real-time based on SessionState events"""

    def __init__(self):
        self.session_state = SessionState()
        self.persistence = SessionPersistence()
        self.classifier = ActivityClassifier()

    def on_new_activity_log(self, activity: ActivityLog):
        """Called every time a new activity is logged"""

        # 3. Feed into SessionState (handles start/end internally)
        self.session_state.add_activity(activity)

        # 4. If a session just ended, persist it + generate commentary
        if self.session_state.prev_session_meta:
            self._handle_session_end(activity_type)

        # 5. Check for inactivity timeout
        self._check_session_timeout()

    def _handle_session_end(self, next_activity_type: str):
        meta = self.session_state.prev_session_meta
        activities = self.session_state.prev_activities

        # Persist the finished session
        name = self.persistence.generate_session_name(activities, meta["session_type"])
        session_id = self.persistence.save_session(
            activities, name, meta["start_time"]
        )

        if session_id:
            # Build metadata for commentary
            total_duration = sum(a.duration_sec for a in activities)
            new_meta = {
                "session_type": next_activity_type,
                "start_time": self.session_state.current_session["start_time"],
                "duration": sum(a.duration_sec for a in self.session_state.get_session_activities())
            }

            # Generate & store commentary
            commentary = generate_transition_commentary(
                meta,
                activities,
                new_meta,
                self.session_state.get_session_activities(),
            )
            add_commentary_to_session(session_id, commentary, datetime.now())

            # Notify user
            NotificationManager().send_macos_notification(
                "Session Reflection", commentary[:200].replace("\n", " ")
            )

        # Clear prev session so we don't repeat
        self.session_state.prev_session_meta = None
        self.session_state.prev_activities = []

    def _check_session_timeout(self):
        """End session if inactive too long"""
        if not self.session_state.has_current_session():
            return

        last = self.session_state.get_last_activity()
        elapsed = datetime.now() - (
            last.timestamp_start + timedelta(seconds=last.duration_sec)
        )
        if elapsed.total_seconds() > self.session_state.session_timeout_seconds:
            print(f"[REALTIME_SESSION] Timeout after {elapsed}, ending session.")
            self.session_state._end_session(datetime.now())

    def force_finalize_session(self):
        """Manually finalize current session (useful for shutdown)"""
        if self.session_state.has_current_session():
            print("[REALTIME_SESSION] Force finalizing session")
            self.session_state._end_session(datetime.now())
