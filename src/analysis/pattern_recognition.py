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
                    session_id=row.session_id,
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

def analyze_and_group_activities_bounded():
    """
    Bounded sessionization - only processes unsessionized gaps with smart boundaries.
    Uses existing session edges as natural buffers to avoid conflicts.
    """
    from ..database.operations import find_smart_sessionization_ranges, fetch_activities_in_time_range
    
    ranges = find_smart_sessionization_ranges()
    if not ranges:
        print("[BOUNDED_SESSIONIZER] No gaps found, all activities sessionized")
        return []
    
    total_sessions_created = 0
    all_created_sessions = []
    
    for start_time, end_time in ranges:
        print(f"[BOUNDED_SESSIONIZER] Processing range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Get activities in this time range
        activities = fetch_activities_in_time_range(start_time, end_time)
        
        if not activities:
            continue
            
        # Sessionize this bounded range
        sessions = batch_sessionize(activities)
        
        # Save sessions and assign activity IDs
        for sess in sessions:
            if not sess:
                continue
                
            # Check if this session contains any unsessionized activities
            has_unsessionized = any(hasattr(a, 'session_id') and a.session_id is None for a in sess)
            
            if has_unsessionized or not hasattr(sess[0], 'session_id'):
                # Create session
                sname = session_name(sess)
                score = weighted_score(sess)
                start = sess[0].timestamp_start
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
                
                # Assign session_id to activities that don't already have one
                activity_ids_to_assign = [
                    a.id for a in sess 
                    if not hasattr(a, 'session_id') or a.session_id is None
                ]
                
                if activity_ids_to_assign:
                    assign_session_to_activities(activity_ids_to_assign, session_id)
                
                all_created_sessions.append({"session_id": session_id, "start": start, "end": end})
                total_sessions_created += 1
    
    print(f"[BOUNDED_SESSIONIZER] Created {total_sessions_created} sessions from {len(ranges)} time ranges")
    return all_created_sessions
