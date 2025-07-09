#!/usr/bin/env python3
"""
Session state management for real-time session grouping,
with psych-backed smoothing + dynamic thresholds.
"""

from collections import deque
from datetime import datetime
from typing import Dict, List, Optional

from ..database.models import ActivityLog
from ..database.operations import save_activity_session


class SessionState:
    """Manages the current session state during real-time grouping"""

    # Hard thresholds (minutes)
    HARD_BREAK_MIN = 10
    HARD_WORK_MIN = 15

    # EMA smoothing factor for per-minute scores
    EMA_ALPHA = 0.3

    # Size of rolling raw score buffer (e.g., last 4h at 1-min interval)
    BUFFER_SIZE = 240

    def __init__(self):
        # Active session data
        self.current_session: Optional[Dict] = None
        self.current_context: Optional[str] = None
        self.context_start_time: Optional[datetime] = None

        # For smoothing + counters
        self.ema_score: Optional[float] = None
        self.break_counter: int = 0
        self.work_counter: int = 0

        # Rolling history of raw scores for dynamic thresholds
        self.score_buffer: deque[float] = deque(maxlen=self.BUFFER_SIZE)

        # Previous session for commentary
        self.prev_session_meta: Optional[Dict] = None
        self.prev_activities: List[ActivityLog] = []

    def _update_ema(self, score: float):
        """Update exponential moving average of productivity score."""
        if self.ema_score is None:
            self.ema_score = score
        else:
            self.ema_score = (
                self.EMA_ALPHA * score + (1 - self.EMA_ALPHA) * self.ema_score
            )

    def _update_buffer(self, score: float):
        """Add raw score to rolling buffer."""
        self.score_buffer.append(score)

    def _compute_dynamic_thresholds(self) -> (float, float):
        """
        Compute dynamic work and break thresholds from raw score history.
        Returns: (work_threshold, break_threshold)
        """
        buf = list(self.score_buffer)
        if len(buf) < 10:
            # Not enough data → fallback to static
            return 20.0, 0.0

        sorted_buf = sorted(buf)
        i75 = int(0.75 * (len(sorted_buf) - 1))
        i25 = int(0.25 * (len(sorted_buf) - 1))
        return sorted_buf[i75], sorted_buf[i25]

    def process_minute(self, activity: ActivityLog, score: Optional[float]):
        """
        Call this once per minute (or per activity) with the latest activity
        and its numeric productivity score (-50..+50).
        """
        now = activity.timestamp_start
        raw_score = float(score or 0)

        # 1. Update EMA and buffer
        self._update_ema(raw_score)
        self._update_buffer(raw_score)

        # 2. Compute dynamic thresholds
        work_thresh, break_thresh = self._compute_dynamic_thresholds()

        # 3. Update counters based on EMA vs thresholds
        if self.ema_score < break_thresh:
            self.break_counter += 1
            self.work_counter = 0
        elif self.ema_score > work_thresh:
            self.work_counter += 1
            self.break_counter = 0
        else:
            # neutral zone decays both counters slightly
            self.break_counter = max(self.break_counter - 1, 0)
            self.work_counter = max(self.work_counter - 1, 0)

        # 4. Use hard thresholds to finalize boundaries
        if self.current_session and self.break_counter >= self.HARD_BREAK_MIN:
            self._end_session(now)
        elif not self.current_session and self.work_counter >= self.HARD_WORK_MIN:
            self._start_session(activity, now)

    def _start_session(self, activity: ActivityLog, start_time: datetime):
        """Begin a new session."""
        # stash old session for commentary
        if self.current_session:
            self.prev_session_meta = {
                "dominant_type": self.current_context,
                "start_time": self.current_session["start_time"],
                "duration": sum(a.duration_sec for a in self.current_session["activities"]),
                "session_type": self.current_context,
            }
            self.prev_activities = list(self.current_session["activities"])
        else:
            self.prev_session_meta = None
            self.prev_activities = []

        # init new session
        self.current_session = {"activities": [activity], "start_time": start_time}
        self.current_context = "productive"
        self.context_start_time = start_time
        print(f"[SessionState] ▶️  Session started at {start_time}")

    def _end_session(self, end_time: datetime):
        """Finalize and persist the current session."""
        acts = self.current_session["activities"]
        start = self.current_session["start_time"]
        total_dur = sum(a.duration_sec for a in acts)
        score = round(
            sum(a.productivity_score * a.duration_sec for a in acts) / total_dur
        )

        session_id = save_activity_session(
            session_name="(AI will name later)",
            productivity_score=score,
            start_time=start,
            end_time=end_time,
            total_duration_sec=total_dur,
            user_confirmed=False,
        )
        print(f"[SessionState] ⏹️  Session {session_id} ended at {end_time}")

        # reset all state
        self.current_session = None
        self.current_context = None
        self.context_start_time = None
        self.break_counter = 0
        self.work_counter = 0
        self.ema_score = None
        self.score_buffer.clear()

    def add_activity(self, activity: ActivityLog):
        """
        Called whenever a new activity arrives; ties into per-minute loop.
        """
        if self.current_session:
            self.current_session["activities"].append(activity)
        self.process_minute(activity, activity.productivity_score)
