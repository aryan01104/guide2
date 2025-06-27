#!/usr/bin/env python3
"""
Configuration settings for the activity tracker
"""

import pathlib
from datetime import timedelta

# Project root directory
PROJECT_ROOT = pathlib.Path(__file__).parent.parent

# Database settings
DATABASE_SETTINGS = {
    'db_path': PROJECT_ROOT / "data" / "activity.db",
    'echo': False  # Set to True for SQL debugging
}

# Logging settings
LOGGING_SETTINGS = {
    'poll_interval_seconds': 10,
    'session_gap_minutes': 15  # Time gap to separate sessions
}

# Flow analysis settings
FLOW_ANALYSIS_SETTINGS = {
    'noise_threshold_seconds': 120,  # Activities under 2 minutes = noise
    'dominance_ratio': 0.75,  # 75% rule for session classification
    'consecutive_time_required': 180,  # 3 minutes for real context switch
    'flow_break_threshold': 180,  # 3+ minutes breaks flow state
    'confidence_threshold': 75  # Auto-classify if confidence > 75%
}

# Real-time session grouping settings
REALTIME_SESSION_SETTINGS = {
    'minimum_focus_time_seconds': 180,  # 3 minutes - minimum time to establish "focus"
    'minimum_break_time_seconds': 120,  # 2 minutes - minimum time to establish "break"
    'context_switch_threshold_seconds': 300,  # 5 minutes - gap that definitively ends a session
    'noise_threshold_seconds': 60,  # 1 minute - ignore brief activities in session grouping
    'session_timeout_seconds': 300,  # 5 minutes - inactivity timeout to auto-finalize session
}

# Notification settings
NOTIFICATION_SETTINGS = {
    'check_interval_minutes': 30,
    'sound_enabled': True,
    'dialog_timeout_seconds': 30
}

# Web interface settings
WEB_SETTINGS = {
    'host': '0.0.0.0',
    'port': 5001,
    'debug': True,
    'calendar_start_hour': 6,
    'calendar_end_hour': 23
}

# Activity classification keywords
PRODUCTIVITY_KEYWORDS = {
    'productive': [
        'localhost', 'github', 'stackoverflow', 'documentation', 
        'vscode', 'terminal', 'python', 'code', 'programming',
        'development', 'docs', 'api', 'database', 'sql'
    ],
    'unproductive': [
        'youtube', 'facebook', 'instagram', 'tiktok', 'netflix', 
        'gaming', 'memes', 'twitter', 'x.com', 'entertainment',
        'sports', 'news', 'reddit'
    ],
    'neutral': [
        'email', 'calendar', 'google', 'search', 'weather',
        'maps', 'settings', 'preferences'
    ]
}

# User configuration settings
USER_CONFIG_SETTINGS = {
    'config_file': PROJECT_ROOT / "data" / "user_config.json",
    'required_fields': [
        'profession', 'main_goal', 'side_aims', 'break_activities'
    ]
}