#!/usr/bin/env python3
"""
Batch sessionizing—simple, robust, human-like.
- Guarantees unique partition of activities into non-overlapping sessions.
- Assigns session_id to every activity, never double-counts.
- Adds post-hoc check for time overlap.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database.operations import get_db_session, save_activity_session, assign_session_to_activities
from ..database.models import ActivityLog
from .flow_analysis import batch_sessionize, weighted_score, session_name, ActivityLogStub

def fetch_activity_logs():
    """
    Fetches all activity logs with duration > 0 from the database,
    returns as ActivityLogStub list.
    """
    session: Session = get_db_session()
    try:
        rows = session.query(ActivityLog).filter(
            ActivityLog.duration_sec > 0
        ).order_by(ActivityLog.timestamp_start).all()
        activities = []
        for row in rows:
            activities.append(
                ActivityLogStub(
                    id=row.id,
                    timestamp_start=row.timestamp_start,
                    duration_sec=row.duration_sec,
                    productivity_score=row.productivity_score,
                    details=row.details,
                )
            )
        return activities
    finally:
        session.close()

def analyze_and_group_activities():
    """
    Main batch sessionizing routine.
    - Uniquely partitions all activities into non-overlapping sessions.
    - Assigns session_id to each activity.
    - Verifies no time overlap between created sessions.
    """
    activities = fetch_activity_logs()
    sessions = batch_sessionize(activities)
    created_sessions = []

    for sess in sessions:
        if not sess:
            continue
        sname = session_name(sess)
        score = weighted_score(sess)
        start = sess[0].timestamp_start
        # Always use last_activity.timestamp_start + duration for true end
        end = sess[-1].timestamp_start + timedelta(seconds=sess[-1].duration_sec)
        total_duration = sum(a.duration_sec for a in sess)
        session_id = save_activity_session(
            session_name=sname,
            productivity_score=score,
            start_time=start,
            end_time=end,
            total_duration_sec=total_duration,
            user_confirmed=False,
        )
        activity_ids = [a.id for a in sess]
        assign_session_to_activities(activity_ids, session_id)
        created_sessions.append({"session_id": session_id, "start": start, "end": end})

    # Overlap check (for debug—delete or keep as assertion)
    sorted_sessions = sorted(created_sessions, key=lambda s: s["start"])
    for i, session in enumerate(sorted_sessions):
        if i > 0 and session["start"] < sorted_sessions[i-1]["end"]:
            print("ERROR: Session overlap detected!", session)

    print(f"[BATCH SESSIONIZER] Grouped {len(activities)} logs into {len(sessions)} sessions.")
    return sessions
