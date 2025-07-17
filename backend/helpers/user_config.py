import json
import pathlib


from ..database.user_config_operations import save_user_config , get_user_config, get_custom_classifications, add_custom_classification

# Legacy JSON path for fallback
CONFIG_PATH = pathlib.Path(__file__).parent.parent / "data" / "user_config.json"


def setup_user_config():
    """Setup user configuration using database"""
    config = load_user_config()
    if config and config.get("profession"):
        print("[CONFIG] User config already exists.")
        return config

    print("Welcome! Let's set up your profile for optimal productivity reflection.\n")

    profession = input("What is your primary field or profession? ").strip()
    main_goal = input("What is your current main goal/project? ").strip()
    side_aims = input("What are some side aims/interests? ").strip()
    break_activities_input = input(
        "What do you do for breaks (comma-separated)? "
    ).strip()
    break_activities = [
        activity.strip() for activity in break_activities_input.split(",")
    ]

    # Save to database
    result = save_user_config(profession, main_goal, side_aims, break_activities)
    if result:
        print("[CONFIG] User config saved to database!")
        return load_user_config()
    else:
        print("[CONFIG] Error saving to database!")
        return None


def load_user_config():
    """Load user configuration from database with JSON fallback"""
    # Try database first
    config = get_user_config()
    if config:
        # Add custom classifications
        custom_classifications = get_custom_classifications()
        config["custom_classifications"] = custom_classifications
        return config

    # Fallback to JSON file if database is empty
    if CONFIG_PATH.exists():
        print("[CONFIG] Database empty, using JSON fallback")
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f)
        except Exception as e:
            print(f"[CONFIG] Error reading JSON fallback: {e}")

    # Return default config if nothing exists
    print("[CONFIG] No config found, using defaults")
    return {
        "profession": "",
        "main_goal": "",
        "side_aims": "",
        "break_activities": [],
        "custom_classifications": {},
    }


def update_custom_classification(activity, classification):
    """Update custom classification in database"""
    # Handle both old string format and new dict format
    if isinstance(classification, dict):
        result = add_custom_classification(
            activity=activity,
            classification=classification.get("classification", "neutral"),
            productivity_score=classification.get("productivity_score"),
            intensity=classification.get("intensity"),
            user_confirmed=True,
        )
    else:
        # Legacy string format
        result = add_custom_classification(
            activity=activity, classification=classification, user_confirmed=True
        )

    if result:
        print(
            f"[CONFIG] Updated classification in database: '{activity}' as {classification}"
        )
    else:
        print(f"[CONFIG] Error updating classification for: '{activity}'")
