#!/usr/bin/env python3
"""
Database operations and utilities
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pathlib

from .models import Base, ActivityLog, CustomClassification, ActivitySession, ActivityPattern, UserConfig

# Database configuration
DB_PATH = pathlib.Path(__file__).parent.parent.parent / "data" / "activity.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database and create tables"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"[DATABASE] Initialized database at {DB_PATH}")

def get_db_session():
    """Get database session"""
    return SessionLocal()

def add_activity_log(timestamp_start: datetime, event_type: str, details: str, 
                    duration_sec: int, productivity_score: int = None, 
                    confidence_score: int = None, classification_text: str = None):
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
            classification_text=classification_text
        )
        session.add(log_entry)
        session.commit()
        # Refresh to get the ID assigned by database
        session.refresh(log_entry)
        return log_entry
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error adding activity log: {e}")
        raise
    finally:
        session.close()

def update_activity_scores(activity_id: int, productivity_score: int, 
                          confidence_score: int = None, classification_text: str = None):
    """Update activity with productivity scores after classification"""
    session = get_db_session()
    try:
        activity = session.query(ActivityLog).filter(ActivityLog.id == activity_id).first()
        if activity:
            activity.productivity_score = productivity_score
            if confidence_score is not None:
                activity.confidence_score = confidence_score
            if classification_text is not None:
                activity.classification_text = classification_text
            session.commit()
            print(f"[DATABASE] Updated activity {activity_id} with score: {productivity_score}, confidence: {confidence_score}")
            
            # Recalculate session scores that include this activity
            recalculate_session_scores_for_activity(activity.timestamp_start)
        else:
            print(f"[DATABASE] Activity {activity_id} not found for score update")
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error updating activity scores: {e}")
        raise
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
        
        sessions_to_update = session.query(ActivitySession).filter(
            ActivitySession.start_time >= start_of_day,
            ActivitySession.start_time <= end_of_day
        ).all()
        
        for activity_session in sessions_to_update:
            # Get all activities within this session's time range
            session_activities = session.query(ActivityLog).filter(
                ActivityLog.timestamp_start >= activity_session.start_time,
                ActivityLog.timestamp_start <= activity_session.end_time
            ).all()
            
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
                print(f"[DATABASE] Recalculated session {activity_session.id} score: {new_session_score} (based on {activities_with_scores} scored activities)")
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error recalculating session scores: {e}")
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
        
        activities = session.query(ActivityLog).filter(
            ActivityLog.timestamp_start >= start_of_day,
            ActivityLog.timestamp_start <= end_of_day
        ).order_by(ActivityLog.timestamp_start).all()
        
        return activities
    finally:
        session.close()

def get_recent_activities(hours_back: int = 2):
    """Get recent activities within specified hours"""
    from datetime import timedelta
    
    session = get_db_session()
    try:
        cutoff = datetime.now() - timedelta(hours=hours_back)
        activities = session.query(ActivityLog).filter(
            ActivityLog.timestamp_start >= cutoff
        ).order_by(ActivityLog.timestamp_start).all()
        
        return activities
    finally:
        session.close()

def get_custom_classification(activity_details: str):
    """Get custom classification for activity"""
    session = get_db_session()
    try:
        classification = session.query(CustomClassification).filter(
            CustomClassification.activity_details == activity_details
        ).first()
        return classification.classification if classification else None
    finally:
        session.close()

def add_custom_classification(activity_details: str, classification: str):
    """Add or update custom classification"""
    session = get_db_session()
    try:
        existing = session.query(CustomClassification).filter(
            CustomClassification.activity_details == activity_details
        ).first()
        
        if existing:
            existing.classification = classification
            existing.updated_at = datetime.utcnow()
        else:
            new_classification = CustomClassification(
                activity_details=activity_details,
                classification=classification
            )
            session.add(new_classification)
        
        session.commit()
        print(f"[DATABASE] Updated custom classification for '{activity_details}' as '{classification}'")
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error updating custom classification: {e}")
        raise
    finally:
        session.close()

def save_activity_session(session_name: str, productivity_score: int, start_time: datetime,
                         end_time: datetime, total_duration_sec: int, user_confirmed: bool = False):
    """Save a grouped activity session"""
    session = get_db_session()
    try:
        activity_session = ActivitySession(
            session_name=session_name,
            productivity_score=productivity_score,
            start_time=start_time,
            end_time=end_time,
            total_duration_sec=total_duration_sec,
            user_confirmed=user_confirmed
        )
        
        session.add(activity_session)
        session.commit()
        
        print(f"[DATABASE] Saved session: {session_name} (score: {productivity_score}, {total_duration_sec//60}min)")
        return activity_session.id
        
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error saving session: {e}")
        return None
    finally:
        session.close()

def get_activity_patterns():
    """Get all learned activity patterns"""
    session = get_db_session()
    try:
        return session.query(ActivityPattern).all()
    finally:
        session.close()

def get_sessions_by_date(date: datetime.date = None):
    """Get all sessions for a specific date"""
    session = get_db_session()
    try:
        if date is None:
            date = datetime.now().date()
        
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        sessions = session.query(ActivitySession).filter(
            ActivitySession.start_time >= start_of_day,
            ActivitySession.start_time <= end_of_day
        ).order_by(ActivitySession.start_time).all()
        
        return sessions
    finally:
        session.close()

def get_session_activities(session_id: int):
    """Get all activities that belong to a specific session"""
    session = get_db_session()
    try:
        # Get the session first
        activity_session = session.query(ActivitySession).filter(
            ActivitySession.id == session_id
        ).first()
        
        if not activity_session:
            return []
        
        # Get activities within the session time range
        activities = session.query(ActivityLog).filter(
            ActivityLog.timestamp_start >= activity_session.start_time,
            ActivityLog.timestamp_start <= activity_session.end_time
        ).order_by(ActivityLog.timestamp_start).all()
        
        return activities
    finally:
        session.close()

def get_pending_sessions():
    """Get sessions that need user confirmation"""
    from datetime import timedelta
    
    session = get_db_session()
    try:
        cutoff = datetime.now() - timedelta(hours=2)
        return session.query(ActivitySession).filter(
            ActivitySession.user_confirmed == False,
            ActivitySession.confidence_score < 75,
            ActivitySession.created_at >= cutoff
        ).all()
    finally:
        session.close()

def update_session_classification(session_id: int, classification: str, user_confirmed: bool = True):
    """Update session classification based on user feedback"""
    session = get_db_session()
    try:
        activity_session = session.query(ActivitySession).filter(
            ActivitySession.id == session_id
        ).first()
        
        if not activity_session:
            return False
        
        activity_session.session_type = classification
        activity_session.user_confirmed = user_confirmed
        activity_session.confidence_score = 100 if user_confirmed else activity_session.confidence_score
        
        session.commit()
        print(f"[DATABASE] Updated session {session_id}: {classification}")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error updating session: {e}")
        return False
    finally:
        session.close()

# ===============================================
# User Configuration Operations
# ===============================================

def get_user_config():
    """Get user configuration from database"""
    session = get_db_session()
    try:
        config = session.query(UserConfig).first()
        if config:
            return {
                'profession': config.profession,
                'main_goal': config.main_goal,
                'side_aims': config.side_aims,
                'break_activities': eval(config.break_activities) if config.break_activities else [],
                'created_at': config.created_at,
                'updated_at': config.updated_at
            }
        return None
    except Exception as e:
        print(f"[DATABASE] Error loading user config: {e}")
        return None
    finally:
        session.close()

def save_user_config(profession, main_goal, side_aims, break_activities):
    """Save or update user configuration in database"""
    session = get_db_session()
    try:
        # Check if config already exists
        existing_config = session.query(UserConfig).first()
        
        if existing_config:
            # Update existing
            existing_config.profession = profession
            existing_config.main_goal = main_goal
            existing_config.side_aims = side_aims
            existing_config.break_activities = str(break_activities)
            existing_config.updated_at = datetime.now()
            config = existing_config
        else:
            # Create new
            config = UserConfig(
                profession=profession,
                main_goal=main_goal,
                side_aims=side_aims,
                break_activities=str(break_activities),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(config)
        
        session.commit()
        print(f"[DATABASE] User config saved successfully")
        return config.id if hasattr(config, 'id') else True
        
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error saving user config: {e}")
        return None
    finally:
        session.close()

def get_custom_classifications():
    """Get all custom classifications from database"""
    session = get_db_session()
    try:
        classifications = session.query(CustomClassification).all()
        result = {}
        for cls in classifications:
            result[cls.activity] = {
                'classification': cls.classification,
                'productivity_score': cls.productivity_score,
                'intensity': cls.intensity,
                'timestamp': cls.timestamp.isoformat() if cls.timestamp else None,
                'user_confirmed': cls.user_confirmed
            }
        return result
    except Exception as e:
        print(f"[DATABASE] Error loading custom classifications: {e}")
        return {}
    finally:
        session.close()

def add_custom_classification(activity, classification, productivity_score=None, intensity=None, user_confirmed=True):
    """Add or update a custom classification"""
    session = get_db_session()
    try:
        # Check if classification already exists
        existing = session.query(CustomClassification).filter_by(activity=activity).first()
        
        if existing:
            # Update existing
            existing.classification = classification
            existing.productivity_score = productivity_score
            existing.intensity = intensity
            existing.user_confirmed = user_confirmed
            existing.timestamp = datetime.now()
            cls_obj = existing
        else:
            # Create new
            cls_obj = CustomClassification(
                activity=activity,
                classification=classification,
                productivity_score=productivity_score,
                intensity=intensity,
                user_confirmed=user_confirmed,
                timestamp=datetime.now()
            )
            session.add(cls_obj)
        
        session.commit()
        print(f"[DATABASE] Custom classification saved: '{activity}' → {classification}")
        return cls_obj.id if hasattr(cls_obj, 'id') else True
        
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error saving custom classification: {e}")
        return None
    finally:
        session.close()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")