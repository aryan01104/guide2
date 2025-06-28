import sys
import os
import traceback
from datetime import datetime

# Ensure src/ is on the import path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from commentator import generate_transition_commentary
from database.models import ActivityLog

def make_activity_log(event_type, details, duration_sec):
    return ActivityLog(
        timestamp_start=datetime.now(),
        event_type=event_type,
        details=details,
        duration_sec=duration_sec,
        productivity_score=None,
        confidence_score=None,
        classification_text=None,
        session_id=None,
    )

def make_session_meta(session_type, duration):
    return {
        'session_type': session_type,
        'duration': duration,
    }

test_cases = [
    {
        'name': 'Productive to Unproductive',
        'prev_session_meta': make_session_meta('productive', 1800),
        'prev_activities': [make_activity_log('app_session', 'VSCode', 1800)],
        'new_session_meta': make_session_meta('unproductive', 900),
        'new_activities': [make_activity_log('app_session', 'YouTube', 900)],
        'should_error': False,
    },
    {
        'name': 'Unproductive to Productive',
        'prev_session_meta': make_session_meta('unproductive', 1200),
        'prev_activities': [make_activity_log('app_session', 'Reddit', 1200)],
        'new_session_meta': make_session_meta('productive', 3600),
        'new_activities': [make_activity_log('app_session', 'PyCharm', 3600)],
        'should_error': False,
    },
    {
        'name': 'Productive to Neutral',
        'prev_session_meta': make_session_meta('productive', 1800),
        'prev_activities': [make_activity_log('app_session', 'Terminal', 1800)],
        'new_session_meta': make_session_meta('neutral', 600),
        'new_activities': [make_activity_log('app_session', 'Gmail', 600)],
        'should_error': False,
    },
    {
        'name': 'Neutral to Productive',
        'prev_session_meta': make_session_meta('neutral', 600),
        'prev_activities': [make_activity_log('app_session', 'Gmail', 600)],
        'new_session_meta': make_session_meta('productive', 2400),
        'new_activities': [make_activity_log('app_session', 'Docs', 2400)],
        'should_error': False,
    },
    {
        'name': 'Productive to Productive',
        'prev_session_meta': make_session_meta('productive', 1800),
        'prev_activities': [make_activity_log('app_session', 'VSCode', 1800)],
        'new_session_meta': make_session_meta('productive', 1200),
        'new_activities': [make_activity_log('app_session', 'Docs', 1200)],
        'should_error': False,
    },
    {
        'name': 'No previous session',
        'prev_session_meta': None,
        'prev_activities': [],
        'new_session_meta': make_session_meta('productive', 1500),
        'new_activities': [make_activity_log('app_session', 'PyCharm', 1500)],
        'should_error': False,
    },
    {
        'name': 'Both sessions empty',
        'prev_session_meta': None,
        'prev_activities': [],
        'new_session_meta': None,
        'new_activities': [],
        'should_error': True,
    },
    {
        'name': 'Multiple activities in sessions',
        'prev_session_meta': make_session_meta('unproductive', 2700),
        'prev_activities': [
            make_activity_log('app_session', 'YouTube', 900),
            make_activity_log('app_session', 'Reddit', 1800),
        ],
        'new_session_meta': make_session_meta('productive', 5400),
        'new_activities': [
            make_activity_log('app_session', 'VSCode', 1800),
            make_activity_log('app_session', 'Docs', 3600),
        ],
        'should_error': False,
    },
    {
        'name': 'Zero duration session',
        'prev_session_meta': make_session_meta('productive', 0),
        'prev_activities': [],
        'new_session_meta': make_session_meta('unproductive', 0),
        'new_activities': [],
        'should_error': True,
    },
]

def run_test():
    print("Running commentary generation tests...")
    failures = []
    for case in test_cases:
        try:
            commentary = generate_transition_commentary(
                case['prev_session_meta'],
                case['prev_activities'],
                case['new_session_meta'],
                case['new_activities']
            )
            if case['should_error']:
                if commentary and isinstance(commentary, str) and commentary.strip():
                    failures.append(
                        f"[{case['name']}] Expected error or empty, got: {commentary}"
                    )
            else:
                if not commentary or not isinstance(commentary, str):
                    failures.append(
                        f"[{case['name']}] Commentary not generated or invalid: {commentary}"
                    )
        except Exception as e:
            tb = traceback.format_exc()
            failures.append(
                f"[{case['name']}] Exception raised:\n{str(e)}\nTraceback:\n{tb}"
            )

    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"\n---\n{f}")
    else:
        print("All commentary generation tests passed.")

if __name__ == '__main__':
    run_test()
