#!/usr/bin/env python3
"""
Session-related database operations
"""


from datetime import datetime, timedelta
from typing import List

import json
from ..llm_client import chat

from .db_config import get_db_session
from .models import ActivityLog, ActivitySession

def save_session(activities: List[ActivityLog]) -> int:
        """Save session to database and return session ID"""

        def save_activity_session(
            session_name: str,
            productivity_score: int,
            start_time: datetime,
            end_time: datetime,
            total_duration_sec: int,
            user_confirmed: bool = False,
            ):
            """Save a grouped activity session"""
            session = get_db_session()
            try:
                activity_session = ActivitySession(
                    session_name=session_name,
                    productivity_score=productivity_score,
                    start_time=start_time,
                    end_time=end_time,
                    total_duration_sec=total_duration_sec,
                    user_confirmed=user_confirmed,
                )

                session.add(activity_session)
                session.commit()

                print(
                    f"[DATABASE] Saved session: {session_name} (score: {productivity_score}, {total_duration_sec//60}min)"
                )
                return activity_session.id

            except Exception as e:
                session.rollback()
                print(f"[DATABASE] Error saving session: {e}")
                return None
            finally:
                session.close()

        def calculate_session_score() -> int:
            """Calculate time-weighted productivity score for session
            
            - preconds: activities is a non empty activitylog list;
            ensure activity corresponds to actual sessions, is not of time <= min
            session time
            - postconds: returns time-weighted sessions score
            """

            # if not activities:
            #     return 0

            total_weighted_score = 0
            total_duration = 0

            for activity in activities:

                # Weight by duration
                total_weighted_score += activity.productivity_score * activity.duration_sec
                total_duration += activity.duration_sec

            # if total_duration == 0:
            #     return 0

            # Calculate weighted average
            avg_score = round(total_weighted_score / total_duration)
            return avg_score
        
        def generate_session_name(activities: List[ActivityLog], dominant_type: str) -> str:
            """
            Generate descriptive session name based on activities via OpenAI.

            CALLER RESP: only after when a sessions has been finalized based on
            sessionizing, and before it has been saved to database, since name is
            neccesary

            Preconditions:
            - activities: list of ActivityLog, may be empty
            - dominant_type: str label of the session

            Postconditions:
            - always returns a non-empty string (uses "Empty Session" if no activities)
            """
            if not activities:
                return "Empty Session"

            # Build a minimal JSON payload of activities
            payload = [
                {
                    "timestamp": a.timestamp_start.isoformat(),
                    "duration_sec": a.duration_sec,
                    "details": a.details
                }
                for a in activities
            ]

            system_prompt = (
                "You are an expert at summarizing a series of user activities into a "
                "concise session title. Each activity has a timestamp, duration, and details. "
                "Return only a short (<5 words) session name that captures the main theme."
            )
            user_prompt = (
                f"Activities (JSON):\n{json.dumps(payload, indent=2)}\n\n"
                f"Dominant type: {dominant_type}\n\n"
                "Give me a one-line session name."
            )

            resp = chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt}
                ],
                temperature=0.0
            )
            # Strip any extra whitespace/newlines
            name = resp.choices[0].message.content.strip()
            return name or "Unnamed Session"
        

        try:
            session_id = save_activity_session(
                session_score = calculate_session_score(activities),
                session_name = generate_session_name(activities),
                start_time = activities[-1].timestamp_start,
                end_time = activities[-1].timestamp_start + timedelta(
                            seconds=activities[-1].duration_sec),
                total_duration_sec = sum(a.duration_sec for a in activities),
                user_confirmed=False,  # Sessions scores are mathematical, not user-confirmed
            )

            print(
                f"[SESSION_PERSISTENCE] ✅ Created session)"
            )

            return session_id

        except Exception as e:
            print(f"[SESSION_PERSISTENCE] ❌ Error in creating-cum-saving session: {e}")
            return None

def get_sessions_by_date(date: datetime.date = None):
    """Get all sessions for a specific date"""
    session = get_db_session()
    try:
        if date is None:
            date = datetime.now().date()

        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())

        sessions = (
            session.query(ActivitySession)
            .filter(
                ActivitySession.start_time >= start_of_day,
                ActivitySession.start_time <= end_of_day,
            )
            .order_by(ActivitySession.start_time)
            .all()
        )

        return sessions
    finally:
        session.close()


def get_session_activities(session_id: int):
    """Get all activities that belong to a specific session"""
    session = get_db_session()
    try:
        activities = (
            session.query(ActivityLog)
            .filter(ActivityLog.session_id == session_id)
            .order_by(ActivityLog.timestamp_start)
            .all()
        )
        return activities
    finally:
        session.close()


def get_pending_sessions():
    """Get sessions that need user confirmation"""
    session = get_db_session()
    try:
        cutoff = datetime.now() - timedelta(hours=2)
        return (
            session.query(ActivitySession)
            .filter(
                ActivitySession.user_confirmed == False,
                ActivitySession.confidence_score < 75,
                ActivitySession.created_at >= cutoff,
            )
            .all()
        )
    finally:
        session.close()


def update_session_classification(
    session_id: int, classification: str, user_confirmed: bool = True
):
    """Update session classification based on user feedback"""
    session = get_db_session()
    try:
        activity_session = (
            session.query(ActivitySession)
            .filter(ActivitySession.id == session_id)
            .first()
        )

        if not activity_session:
            return False

        activity_session.session_type = classification
        activity_session.user_confirmed = user_confirmed
        activity_session.confidence_score = (
            100 if user_confirmed else activity_session.confidence_score
        )

        session.commit()
        print(f"[DATABASE] Updated session {session_id}: {classification}")
        return True

    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error updating session: {e}")
        return False
    finally:
        session.close()


def add_commentary_to_session(
    session_id: int, commentary: str, commentary_time: datetime
):
    """Add commentary to a session"""
    session = get_db_session()
    try:
        sess = (
            session.query(ActivitySession)
            .filter(ActivitySession.id == session_id)
            .first()
        )
        if sess:
            sess.commentary = commentary
            sess.commentary_time = commentary_time
            session.commit()
    finally:
        session.close()


def recalculate_session_scores_for_activity(activity_timestamp: datetime):
    """Recalculate session scores for sessions that might contain the given activity"""
    session = get_db_session()
    try:
        # Find sessions that might contain this activity (same day)
        activity_date = activity_timestamp.date()
        start_of_day = datetime.combine(activity_date, datetime.min.time())
        end_of_day = datetime.combine(activity_date, datetime.max.time())

        sessions_to_update = (
            session.query(ActivitySession)
            .filter(
                ActivitySession.start_time >= start_of_day,
                ActivitySession.start_time <= end_of_day,
            )
            .all()
        )

        for activity_session in sessions_to_update:
            # Get all activities within this session's time range
            session_activities = (
                session.query(ActivityLog)
                .filter(
                    ActivityLog.timestamp_start >= activity_session.start_time,
                    ActivityLog.timestamp_start <= activity_session.end_time,
                )
                .all()
            )

            # Calculate time-weighted average score
            total_time = 0
            weighted_score_sum = 0
            activities_with_scores = 0

            for act in session_activities:
                if act.productivity_score is not None:
                    total_time += act.duration_sec
                    weighted_score_sum += act.productivity_score * act.duration_sec
                    activities_with_scores += 1

            # Update session score if we have scored activities
            if total_time > 0 and activities_with_scores > 0:
                new_session_score = round(weighted_score_sum / total_time)
                activity_session.productivity_score = new_session_score
                print(
                    f"[DATABASE] Recalculated session {activity_session.id} score: {new_session_score} (based on {activities_with_scores} scored activities)"
                )

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error recalculating session scores: {e}")
        raise
    finally:
        session.close()


def find_smart_sessionization_ranges():
    """Find time ranges using existing session boundaries as natural buffers"""
    session = get_db_session()
    try:
        # Get unsessionized activity gaps
        unsessionized = (
            session.query(ActivityLog)
            .filter(ActivityLog.session_id == None, ActivityLog.duration_sec > 0)
            .order_by(ActivityLog.timestamp_start)
            .all()
        )

        if not unsessionized:
            return []

        ranges = []
        one_day = timedelta(days=1)
        fallback_buffer = timedelta(hours=2)

        # Group consecutive unsessionized activities
        current_gap_start = unsessionized[0].timestamp_start
        prev_timestamp = unsessionized[0].timestamp_start

        for i, activity in enumerate(unsessionized[1:], 1):
            time_gap = (activity.timestamp_start - prev_timestamp).total_seconds()

            if time_gap > 1800:  # 30min gap = separate processing range
                # Process current gap
                gap_end = prev_timestamp + timedelta(
                    seconds=unsessionized[i - 1].duration_sec
                )
                process_range = calculate_processing_bounds(
                    session, current_gap_start, gap_end, one_day, fallback_buffer
                )
                ranges.append(process_range)

                # Start new gap
                current_gap_start = activity.timestamp_start

            prev_timestamp = activity.timestamp_start

        # Process final gap
        final_gap_end = unsessionized[-1].timestamp_start + timedelta(
            seconds=unsessionized[-1].duration_sec
        )
        final_range = calculate_processing_bounds(
            session, current_gap_start, final_gap_end, one_day, fallback_buffer
        )
        ranges.append(final_range)

        return ranges
    finally:
        session.close()


def calculate_processing_bounds(session, gap_start, gap_end, one_day, fallback_buffer):
    """Calculate smart processing boundaries for a gap"""

    # Find last session ending before gap_start (within 1 day)
    boundary_start = (
        session.query(ActivitySession.end_time)
        .filter(
            ActivitySession.end_time <= gap_start,
            ActivitySession.end_time >= gap_start - one_day,
        )
        .order_by(ActivitySession.end_time.desc())
        .first()
    )

    if boundary_start:
        process_start = boundary_start[0]  # Use session end_time
    else:
        process_start = gap_start - fallback_buffer  # Fallback to 2hr buffer

    # Find first session starting after gap_end (within 1 day)
    boundary_end = (
        session.query(ActivitySession.start_time)
        .filter(
            ActivitySession.start_time >= gap_end,
            ActivitySession.start_time <= gap_end + one_day,
        )
        .order_by(ActivitySession.start_time.asc())
        .first()
    )

    if boundary_end:
        process_end = boundary_end[0]  # Use session start_time
    else:
        process_end = gap_end + fallback_buffer  # Fallback to 2hr buffer

    return (process_start, process_end)
