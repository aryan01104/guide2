#!/usr/bin/env python3
"""
Utility functions and helpers
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default or []


def safe_json_dumps(data: Any, default: str = "[]") -> str:
    """Safely dump data to JSON string with fallback"""
    try:
        return json.dumps(data)
    except (TypeError, ValueError):
        return default


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        if "://" in url:
            domain = url.split("://")[1].split("/")[0]
            return domain.replace("www.", "")
        return None
    except (IndexError, AttributeError):
        return None


def extract_app_name(details: str) -> str:
    """Extract app name from activity details"""
    if "|" in details:
        parts = details.split("|")
        if len(parts) > 1:
            app_or_title = parts[1].strip()
            return app_or_title.split()[0] if app_or_title else "Unknown"
    return "Unknown"


def clean_activity_text(text: str, max_length: int = 50) -> str:
    """Clean and truncate activity text for display"""
    cleaned = text.replace("|", " - ")
    if len(cleaned) > max_length:
        return cleaned[:max_length] + "..."
    return cleaned


def calculate_time_overlap(
    start1: datetime, end1: datetime, start2: datetime, end2: datetime
) -> timedelta:
    """Calculate overlap between two time periods"""
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)

    if overlap_start < overlap_end:
        return overlap_end - overlap_start
    return timedelta(0)


def group_by_time_gap(
    activities: List[Any], gap_minutes: int = 15, time_attr: str = "timestamp_start"
) -> List[List[Any]]:
    """Group activities by time gaps"""
    if not activities:
        return []

    # Sort by timestamp
    sorted_activities = sorted(activities, key=lambda x: getattr(x, time_attr))

    groups = []
    current_group = [sorted_activities[0]]

    for activity in sorted_activities[1:]:
        current_time = getattr(activity, time_attr)
        last_time = getattr(current_group[-1], time_attr)

        time_gap = (current_time - last_time).total_seconds() / 60

        if time_gap <= gap_minutes:
            current_group.append(activity)
        else:
            groups.append(current_group)
            current_group = [activity]

    groups.append(current_group)
    return groups


def calculate_productivity_stats(
    activities: List[Any], category_attr: str = "category"
) -> Dict[str, float]:
    """Calculate productivity statistics for a list of activities"""
    total_time = sum(getattr(activity, "duration_sec", 0) for activity in activities)

    if total_time == 0:
        return {
            "total_hours": 0,
            "productive_hours": 0,
            "unproductive_hours": 0,
            "unclear_hours": 0,
            "productive_percent": 0,
        }

    productive_time = 0
    unproductive_time = 0

    for activity in activities:
        category = (getattr(activity, category_attr, "") or "").lower()
        duration = getattr(activity, "duration_sec", 0)

        if "productive" in category and "unproductive" not in category:
            productive_time += duration
        elif "unproductive" in category:
            unproductive_time += duration

    unclear_time = total_time - productive_time - unproductive_time

    return {
        "total_hours": round(total_time / 3600, 1),
        "productive_hours": round(productive_time / 3600, 1),
        "unproductive_hours": round(unproductive_time / 3600, 1),
        "unclear_hours": round(unclear_time / 3600, 1),
        "productive_percent": round((productive_time / total_time * 100), 1),
    }


def validate_date_string(date_str: str) -> Optional[datetime]:
    """Validate and parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def get_time_range_for_date(date: datetime) -> tuple:
    """Get start and end datetime for a given date"""
    start_of_day = datetime.combine(date.date(), datetime.min.time())
    end_of_day = datetime.combine(date.date(), datetime.max.time())
    return start_of_day, end_of_day
