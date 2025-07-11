#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Activity log database operations

Functions:
    - add_activity_log: Insert a new ActivityLog entry into the database.
    - update_activity_scores: Update an activity’s productivity scores and 
        recalculate session metrics.
    - get_activities_by_date: Retrieve all ActivityLog entries for a given date.
    - get_recent_activities: Fetch recent ActivityLog entries within the last 
        N hours, optionally only unassigned.
    - assign_session_to_activities: Bulk‐assign a session_id to a list of 
        ActivityLog records.
    - fetch_activities_in_time_range: Load activities in a time window and wrap 
        them as ActivityLogStub objects.
"""

from datetime import datetime, timedelta
from typing import List

from .db_config import get_db_session
from .models import ActivityLog


def add_activity_log(
    timestamp_start: datetime,
    event_type: str,
    details: str,
    duration_sec: int,
    productivity_score: int = None,
    confidence_score: int = None,
    classification_text: str = None,
):
    """Add new activity log entry"""
    
    session = get_db_session()
    try:
        log_entry = ActivityLog(
            timestamp_start=timestamp_start,
            event_type=event_type,
            details=details,
            duration_sec=duration_sec,
            productivity_score=productivity_score,
            confidence_score=confidence_score,
            classification_text=classification_text,
        )
        session.add(log_entry)
        session.commit()
        session.refresh(log_entry)
        return log_entry
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error adding activity log: {e}")
        raise
    finally:
        session.close()


def update_activity_scores(
    activity_id: int,
    productivity_score: int,
    confidence_score: int = None,
    classification_text: str = None,
):
    """Update activity with productivity scores after classification"""
    session = get_db_session()
    try:
        activity = (
            session.query(ActivityLog).filter(ActivityLog.id == activity_id).first()
        )
        if activity:
            activity.productivity_score = productivity_score
            if confidence_score is not None:
                activity.confidence_score = confidence_score
            if classification_text is not None:
                activity.classification_text = classification_text
            session.commit()
            print(
                f"[DATABASE] Updated activity {activity_id} with score: {productivity_score}, confidence: {confidence_score}"
            )

            # Import here to avoid circular dependency
            from .session_operations import \
                recalculate_session_scores_for_activity

            recalculate_session_scores_for_activity(activity.timestamp_start)
        else:
            print(f"[DATABASE] Activity {activity_id} not found for score update")
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error updating activity scores: {e}")
        raise
    finally:
        session.close()


def get_activities_by_date(date: datetime.date = None):
    """Get all activities for a specific date"""
    session = get_db_session()
    try:
        if date is None:
            date = datetime.now().date()

        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())

        activities = (
            session.query(ActivityLog)
            .filter(
                ActivityLog.timestamp_start >= start_of_day,
                ActivityLog.timestamp_start <= end_of_day,
            )
            .order_by(ActivityLog.timestamp_start)
            .all()
        )

        return activities
    finally:
        session.close()


def get_recent_activities(hours_back: int = 2, only_unassigned: bool = True):
    """Get recent activities within specified time window"""
    session = get_db_session()
    try:
        cutoff = datetime.now() - timedelta(hours=hours_back)
        q = session.query(ActivityLog).filter(ActivityLog.timestamp_start >= cutoff)
        if only_unassigned:
            q = q.filter(ActivityLog.session_id == None)
        activities = q.order_by(ActivityLog.timestamp_start).all()
        return activities
    finally:
        session.close()


def assign_session_to_activities(activity_ids: List[int], session_id: int):
    """Assign session_id to activities"""
    session = get_db_session()
    try:
        session.query(ActivityLog).filter(ActivityLog.id.in_(activity_ids)).update(
            {"session_id": session_id}, synchronize_session=False
        )
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error assigning session_id: {e}")
    finally:
        session.close()


def fetch_activities_in_time_range(start_time: datetime, end_time: datetime):
    """Fetch activities within time range for bounded sessionization"""
    session = get_db_session()
    try:
        activities = (
            session.query(ActivityLog)
            .filter(
                ActivityLog.timestamp_start >= start_time,
                ActivityLog.timestamp_start <= end_time,
                ActivityLog.duration_sec > 0,
            )
            .order_by(ActivityLog.timestamp_start)
            .all()
        )

        from ..analysis.flow_analysis import ActivityLogStub

        return [
            ActivityLogStub(
                id=row.id,
                timestamp_start=row.timestamp_start,
                duration_sec=row.duration_sec,
                productivity_score=row.productivity_score,
                details=row.details,
                session_id=row.session_id,
            )
            for row in activities
        ]
    finally:
        session.close()



