#!/usr/bin/env python3
"""
Legacy database operations - imports from modularized components
"""

# Import all operations from modularized components for backward compatibility
from .activity_operations import (add_activity_log,
                                  assign_session_to_activities,
                                  fetch_activities_in_time_range,
                                  get_activities_by_date,
                                  get_recent_activities,
                                  update_activity_scores)
from .db_config import get_db_session, init_database
from .pattern_operations import get_activity_patterns
from .session_operations import (add_commentary_to_session,
                                 find_smart_sessionization_ranges,
                                 get_pending_sessions, get_session_activities,
                                 get_sessions_by_date,
                                 recalculate_session_scores_for_activity,
                                 update_session_classification)
from .user_config_operations import (add_custom_classification,
                                     add_custom_classification_with_score,
                                     get_custom_classification,
                                     get_custom_classifications,
                                     get_user_config, save_user_config)

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")
