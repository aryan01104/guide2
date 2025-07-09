#!/usr/bin/env python3
"""
User configuration database operations
"""

from datetime import datetime

from .db_config import get_db_session
from .models import CustomClassification, UserConfig


def get_user_config():
    """Get user configuration from database"""
    session = get_db_session()
    try:
        config = session.query(UserConfig).first()
        if config:
            return {
                "profession": config.profession,
                "main_goal": config.main_goal,
                "side_aims": config.side_aims,
                "break_activities": (
                    eval(config.break_activities) if config.break_activities else []
                ),
                "created_at": config.created_at,
                "updated_at": config.updated_at,
            }
        return None
    except Exception as e:
        print(f"[DATABASE] Error loading user config: {e}")
        return None
    finally:
        session.close()


def save_user_config(
    profession: str, main_goal: str, side_aims: str, break_activities: list
):
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
                updated_at=datetime.now(),
            )
            session.add(config)

        session.commit()
        print(f"[DATABASE] User config saved successfully")
        return config.id if hasattr(config, "id") else True

    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error saving user config: {e}")
        return None
    finally:
        session.close()


def get_custom_classification(activity_details: str):
    """Get custom classification for activity"""
    session = get_db_session()
    try:
        classification = (
            session.query(CustomClassification)
            .filter(CustomClassification.activity_details == activity_details)
            .first()
        )
        return classification.classification if classification else None
    finally:
        session.close()


def add_custom_classification(activity_details: str, classification: str):
    """Add or update custom classification"""
    session = get_db_session()
    try:
        existing = (
            session.query(CustomClassification)
            .filter(CustomClassification.activity_details == activity_details)
            .first()
        )

        if existing:
            existing.classification = classification
            existing.updated_at = datetime.utcnow()
        else:
            new_classification = CustomClassification(
                activity_details=activity_details, classification=classification
            )
            session.add(new_classification)

        session.commit()
        print(
            f"[DATABASE] Updated custom classification for '{activity_details}' as '{classification}'"
        )
    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error updating custom classification: {e}")
        raise
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
                "classification": cls.classification,
                "productivity_score": cls.productivity_score,
                "intensity": cls.intensity,
                "timestamp": cls.timestamp.isoformat() if cls.timestamp else None,
                "user_confirmed": cls.user_confirmed,
            }
        return result
    except Exception as e:
        print(f"[DATABASE] Error loading custom classifications: {e}")
        return {}
    finally:
        session.close()


def add_custom_classification_with_score(
    activity: str,
    classification: str,
    productivity_score: int = None,
    intensity: str = None,
    user_confirmed: bool = True,
):
    """Add or update a custom classification with productivity score"""
    session = get_db_session()
    try:
        # Check if classification already exists
        existing = (
            session.query(CustomClassification).filter_by(activity=activity).first()
        )

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
                timestamp=datetime.now(),
            )
            session.add(cls_obj)

        session.commit()
        print(
            f"[DATABASE] Custom classification saved: '{activity}' → {classification}"
        )
        return cls_obj.id if hasattr(cls_obj, "id") else True

    except Exception as e:
        session.rollback()
        print(f"[DATABASE] Error saving custom classification: {e}")
        return None
    finally:
        session.close()
