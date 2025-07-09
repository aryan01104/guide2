#!/usr/bin/env python3
"""
Pattern analysis database operations
"""

from .db_config import get_db_session
from .models import ActivityPattern


def get_activity_patterns():
    """Get all learned activity patterns"""
    session = get_db_session()
    try:
        return session.query(ActivityPattern).all()
    finally:
        session.close()
