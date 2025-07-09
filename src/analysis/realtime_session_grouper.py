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
from .session_decision_engine import SessionDecisionEngine
from ..to_database.session_persistence import SessionPersistence
from .session_state import SessionState


class RealTimeSessionGrouper:
    """Groups activities into sessions in real-time based on context switches"""

    def __init__(self):
        # Initialize components
        self.session_state = SessionState()
        self.decision_engine = SessionDecisionEngine()
        self.persistence = SessionPersistence()
        self.classifier = ActivityClassifier()

    def on_new_activity(self, activity: ActivityLog):
        """Called every time a new activity is logged"""

        # 1. Skip noise activities
        if self.decision_engine.is_noise_activity(activity):
            print(
                f"[REALTIME_SESSION] Ignoring noise activity: {activity.details} ({activity.duration_sec}s)"
            )
            return

        # 2. Get activity classification
        activity_type = self.classifier.classify_activity_type(activity)
        print(
            f"[REALTIME_SESSION] Activity: {activity.details} classified as: {activity_type}"
        )

        # 3. Determine if context switch occurred
        if self.session_state.current_context is None:
            # First activity - start new session
            print(
                f"[REALTIME_SESSION] Starting first session with {activity_type} activity"
            )
            self._start_new_session_with_commentary(activity, activity_type)

        elif activity_type != self.session_state.current_context:
            # Different context - check if we should switch
            time_in_current_context = (
                activity.timestamp_start - self.session_state.context_start_time
            ).total_seconds()

            print(
                f"[REALTIME_SESSION] Context switch detected: {self.session_state.current_context} -> {activity_type}"
            )
            print(
                f"[REALTIME_SESSION] Time in current context: {time_in_current_context}s"
            )

            if self.decision_engine.should_create_session(
                self.session_state.current_context,
                time_in_current_context,
                activity_type,
            ):
                # End current session and start new one
                print(f"[REALTIME_SESSION] Creating session boundary")
                self.finalize_current_session()
                self._start_new_session_with_commentary(activity, activity_type)
            else:
                # Too brief - might be temporary distraction
                print(
                    f"[REALTIME_SESSION] Adding to pending activities (too brief for context switch)"
                )
                self.session_state.pending_activities.append(activity)

        else:
            # Same context - continue current session
            print(f"[REALTIME_SESSION] Continuing {activity_type} session")
            self.session_state.add_to_current_session(activity)

        # 4. Check for session timeout
        self.check_session_timeout()

    def _start_new_session_with_commentary(
        self, activity: ActivityLog, activity_type: str
    ):
        """Start new session and handle commentary generation"""
        # Start the new session
        self.session_state.start_new_session(activity, activity_type)

        # Add any pending activities if they match new context
        matching_pending = self.decision_engine.should_add_pending_activities(
            self.session_state.pending_activities,
            activity_type,
            self.classifier.classify_activity_type,
        )

        if matching_pending:
            print(
                f"[REALTIME_SESSION] Adding {len(matching_pending)} pending activities to new session"
            )
            for pending_activity in matching_pending:
                self.session_state.add_to_current_session(pending_activity)

            # Remove matched activities from pending
            self.session_state.pending_activities = [
                a
                for a in self.session_state.pending_activities
                if self.classifier.classify_activity_type(a) != activity_type
            ]

        print(f"[REALTIME_SESSION] Started new {activity_type} session")

        # Generate commentary if there was a previous session
        self._generate_commentary_if_applicable(activity_type)

    def _generate_commentary_if_applicable(self, activity_type: str):
        """Generate commentary for session transitions"""
        if not (
            self.session_state.prev_session_meta or self.session_state.prev_activities
        ):
            return

        # Save new session now to DB to get new_session_id
        activities = self.session_state.get_session_activities()
        session_name = self.persistence.generate_session_name(activities, activity_type)

        session_id = self.persistence.save_session(
            activities, session_name, self.session_state.current_session["start_time"]
        )

        if session_id:
            # Prepare session metadata for commentary
            total_duration = sum(a.duration_sec for a in activities)
            new_session_meta = {
                "dominant_type": activity_type,
                "start_time": self.session_state.current_session["start_time"],
                "duration": total_duration,
                "session_type": activity_type,
            }

            # 1. Generate commentary
            commentary = generate_transition_commentary(
                self.session_state.prev_session_meta,
                self.session_state.prev_activities,
                new_session_meta,
                activities,
            )

            # 2. Store commentary in DB
            add_commentary_to_session(session_id, commentary, datetime.now())

            # 3. Notify user (short version)
            notif = NotificationManager()
            notif.send_macos_notification(
                "Session Reflection", commentary[:200].replace("\n", " ")
            )

        # Reset previous session info
        self.session_state.prev_session_meta = None
        self.session_state.prev_activities = []

    def finalize_current_session(self):
        """Complete current session and save to database"""
        if not self.session_state.has_current_session():
            return

        activities = self.session_state.get_session_activities()
        dominant_type = self.session_state.current_session["dominant_type"]
        start_time = self.session_state.current_session["start_time"]

        # Generate session name and save
        session_name = self.persistence.generate_session_name(activities, dominant_type)
        self.persistence.save_session(activities, session_name, start_time)

        # Clear current session
        self.session_state.clear_current_session()

    def check_session_timeout(self):
        """Check if current session has timed out due to inactivity"""
        if not self.session_state.has_current_session():
            return

        last_activity = self.session_state.get_last_activity()
        if self.decision_engine.is_session_timeout(last_activity):
            time_since_last = datetime.now() - (
                last_activity.timestamp_start
                + timedelta(seconds=last_activity.duration_sec)
            )
            print(
                f"[REALTIME_SESSION] Session timeout after {time_since_last} of inactivity"
            )
            self.finalize_current_session()

    def force_finalize_session(self):
        """Manually finalize current session (useful for shutdown)"""
        if self.session_state.has_current_session():
            print("[REALTIME_SESSION] Force finalizing current session")
            self.finalize_current_session()
