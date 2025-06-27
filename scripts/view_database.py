#!/usr/bin/env python3
"""
Database viewer script
"""

import sys
import pathlib
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src.database.operations import get_db_session
from src.database.models import ActivityLog, ActivitySession, ActivityPattern, CustomClassification

def view_recent_activities(limit=10):
    """View recent activity logs"""
    session = get_db_session()
    try:
        activities = session.query(ActivityLog).order_by(
            ActivityLog.timestamp_start.desc()
        ).limit(limit).all()
        
        print(f"\n📋 Recent {len(activities)} Activities:")
        print("-" * 100)
        for activity in activities:
            duration_min = activity.duration_sec // 60
            print(f"{activity.timestamp_start.strftime('%Y-%m-%d %H:%M')} | "
                  f"{duration_min:3d}m | {activity.event_type:20s} | "
                  f"{getattr(activity, 'productivity_score', 'N/A'):4s} | "
                  f"{activity.details[:50]}")
    finally:
        session.close()

def view_sessions(limit=10):
    """View activity sessions"""
    session = get_db_session()
    try:
        sessions = session.query(ActivitySession).order_by(
            ActivitySession.start_time.desc()
        ).limit(limit).all()
        
        print(f"\n🎯 Recent {len(sessions)} Sessions:")
        print("-" * 100)
        for sess in sessions:
            duration_min = sess.total_duration_sec // 60
            status = "✅" if sess.user_confirmed else "❓"
            print(f"{sess.start_time.strftime('%Y-%m-%d %H:%M')} | "
                  f"{duration_min:3d}m | {sess.confidence_score:3d}% | "
                  f"{status} | {sess.session_type:12s} | {sess.session_name}")
    finally:
        session.close()

def view_patterns():
    """View learned patterns"""
    session = get_db_session()
    try:
        patterns = session.query(ActivityPattern).order_by(
            ActivityPattern.usage_count.desc()
        ).all()
        
        print(f"\n🧠 Learned Patterns ({len(patterns)}):")
        print("-" * 80)
        for pattern in patterns:
            print(f"{pattern.pattern_name:30s} | {pattern.session_type:12s} | "
                  f"Used: {pattern.usage_count:2d}x | Success: {pattern.success_rate}%")
    finally:
        session.close()

def view_database_stats():
    """View database statistics"""
    session = get_db_session()
    try:
        total_activities = session.query(ActivityLog).count()
        total_sessions = session.query(ActivitySession).count()
        total_patterns = session.query(ActivityPattern).count()
        total_custom = session.query(CustomClassification).count()
        
        print("\n📊 Database Statistics:")
        print("-" * 30)
        print(f"Activities logged: {total_activities}")
        print(f"Sessions created:  {total_sessions}")
        print(f"Patterns learned:  {total_patterns}")
        print(f"Custom rules:      {total_custom}")
        
        # Recent activity summary
        from datetime import timedelta
        recent_cutoff = datetime.now() - timedelta(days=1)
        recent_activities = session.query(ActivityLog).filter(
            ActivityLog.timestamp_start >= recent_cutoff
        ).count()
        print(f"Last 24h activities: {recent_activities}")
        
    finally:
        session.close()

def main():
    """Main database viewer"""
    print("🗄️  Activity Tracker Database Viewer")
    print("=" * 50)
    
    view_database_stats()
    view_recent_activities(10)
    view_sessions(5)
    view_patterns()
    
    print(f"\n💡 Database location: {pathlib.Path('data/activity.db').absolute()}")

if __name__ == "__main__":
    main()