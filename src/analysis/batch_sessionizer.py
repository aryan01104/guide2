#!/usr/bin/env python3
"""
Batch sessionizing and flow-aware analysis for processing historical data
"""

from datetime import datetime, timedelta
from typing import List, Optional

# Configuration
GAP_THRESHOLD_SEC = 1800
MICRO_BREAK_THRESHOLD_SEC = 300


class ActivityLogStub:
    """
    Lightweight, in-memory representation of an activity log entry.

    Used for batch processing, sessionizing, or analysis without hitting the DB repeatedly.
    """

    def __init__(
        self,
        id: int,
        timestamp_start: datetime,
        duration_sec: int,
        productivity_score: Optional[int],
        details: str,
        session_id: Optional[int] = None,
    ):
        self.id = id
        self.timestamp_start = timestamp_start
        self.duration_sec = duration_sec
        self.productivity_score = productivity_score
        self.details = details
        self.session_id = session_id

    @property
    def end_time(self):
        return self.timestamp_start + timedelta(seconds=self.duration_sec)


def classify_type(prod_score: Optional[int]) -> str:
    """Convert numerical productivity score to classification type"""
    if prod_score is None:
        return "neutral"
    if prod_score >= 20:
        return "productive"
    elif prod_score <= -20:
        return "unproductive"
    else:
        return "neutral"


def batch_sessionize(
    activities: List[ActivityLogStub],
    gap_threshold_sec: int = GAP_THRESHOLD_SEC,
    micro_break_threshold_sec: int = MICRO_BREAK_THRESHOLD_SEC,
) -> List[List[ActivityLogStub]]:
    """
    Groups activities into contiguous sessions using time and type.

    - Sorts activities chronologically.
    - Starts a new session when:
        - The gap between activities exceeds `gap_threshold_sec`, or
        - The activity type changes (productive ↔ unproductive), unless the new
          activity is a short "micro-activity" (<= `micro_break_threshold_sec`)
          matching the original session type.
    - Treats micro-activities as "blips" if they don't indicate a real context
      switch.
    - Returns: list of session-lists (each a group of activities).

    Ensures sessions are logically grouped for true context, not fragmented by
    brief distractions.
    """
    if not activities:
        return []

    activities = sorted(activities, key=lambda a: a.timestamp_start)
    sessions = []
    buffer = [activities[0]]

    for i in range(1, len(activities)):
        prev = buffer[-1]
        curr = activities[i]
        gap = (curr.timestamp_start - prev.end_time).total_seconds()

        if gap > gap_threshold_sec:
            sessions.append(buffer)
            buffer = [curr]
            continue

        prev_type = classify_type(prev.productivity_score)
        curr_type = classify_type(curr.productivity_score)

        if prev_type != curr_type:
            # Merge micro-distractions and micro-breaks
            if (
                curr.duration_sec <= micro_break_threshold_sec
                and prev_type == classify_type(buffer[0].productivity_score)
            ):
                buffer.append(curr)
                continue
            if (
                prev.duration_sec <= micro_break_threshold_sec
                and curr_type == classify_type(buffer[0].productivity_score)
            ):
                buffer.append(curr)
                continue
            sessions.append(buffer)
            buffer = [curr]
        else:
            buffer.append(curr)

    if buffer:
        sessions.append(buffer)

    return sessions


def calculate_weighted_score(session: List[ActivityLogStub]) -> int:
    """Calculate time-weighted productivity score for session"""
    total = sum(a.duration_sec for a in session)
    if not total:
        return 0
    return round(
        sum((a.productivity_score or 0) * a.duration_sec for a in session) / total
    )


def generate_session_name(session: List[ActivityLogStub]) -> str:
    """Generate descriptive session name based on activity patterns"""
    if not session:
        return "Empty Session"

    details_text = " ".join(a.details.lower() for a in session)

    if "code" in details_text:
        return "Coding Session"
    elif "chrome" in details_text or "stackoverflow" in details_text:
        return "Research Session"
    elif (
        sum(1 for a in session if classify_type(a.productivity_score) == "productive")
        > len(session) // 2
    ):
        return "Work Session"
    elif (
        sum(1 for a in session if classify_type(a.productivity_score) == "unproductive")
        > len(session) // 2
    ):
        return "Break Session"

    return "Mixed Session"
