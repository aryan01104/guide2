#!/usr/bin/env python3
"""
Batch sessionizing—simple, robust, human-like.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from ..database.operations import get_db_session, save_activity_session
from ..database.models import ActivityLog
from .flow_analysis import batch_sessionize, weighted_score, session_name, ActivityLogStub

def fetch_activity_logs():
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
    activities = fetch_activity_logs()
    sessions = batch_sessionize(activities)
    for sess in sessions:
        if not sess: continue
        sname = session_name(sess)
        score = weighted_score(sess)
        start = sess[0].timestamp_start
        end = sess[-1].end_time
        total_duration = sum(a.duration_sec for a in sess)
        save_activity_session(
            session_name=sname,
            productivity_score=score,
            start_time=start,
            end_time=end,
            total_duration_sec=total_duration,
            user_confirmed=False,
        )
    print(f"[BATCH SESSIONIZER] Grouped {len(activities)} logs into {len(sessions)} sessions.")
    return sessions
