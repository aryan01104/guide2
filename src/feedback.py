import csv
import os
from datetime import datetime
from .user_config import update_custom_classification
from scheduler import FEEDBACK_PATH

def ask_for_feedback():
    print("[FEEDBACK] Starting user feedback session.")
    if not os.path.exists(FEEDBACK_PATH):
        print("[FEEDBACK] No unclassified activities for feedback.")
        return
    rows = []
    with open(FEEDBACK_PATH, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for _, activity in reader:
            rows.append(activity)
    if not rows:
        print("[FEEDBACK] No activities for feedback.")
        return
    
    print("\nHelp improve your productivity assistant! Rate these activities:")
    print("=" * 60)
    print("Rating Scale:")
    print("  -50: Very unproductive (major distraction)")
    print("  -25: Somewhat unproductive (minor distraction)")
    print("    0: Neutral (necessary but not advancing goals)")
    print("  +25: Somewhat productive (helpful for goals)")
    print("  +50: Very productive (major progress on goals)")
    print("=" * 60)
    
    for a in set(rows):
        while True:
            try:
                print(f"\nActivity: \"{a}\"")
                score = input("Rate productivity (-50 to +50, or 'skip'): ").strip().lower()
                
                if score == 'skip':
                    print(f"[FEEDBACK] Skipped: '{a}'")
                    break
                
                score = int(score)
                if -50 <= score <= 50:
                    # Convert score to classification and intensity
                    classification, intensity = score_to_classification(score)
                    
                    # Store enhanced classification data
                    update_enhanced_classification(a, {
                        'classification': classification,
                        'productivity_score': score,
                        'intensity': intensity,
                        'timestamp': str(datetime.now())
                    })
                    
                    print(f"[FEEDBACK] Updated: '{a}' → {classification} (score: {score}, intensity: {intensity})")
                    break
                else:
                    print("Please enter a number between -50 and +50")
                    
            except ValueError:
                print("Please enter a valid number or 'skip'")
    
    os.remove(FEEDBACK_PATH)
    print("\n[FEEDBACK] Finished updating feedback. Thank you!")

def score_to_classification(score):
    """Convert productivity score to classification and intensity"""
    if score >= 25:
        return "productive", "high"
    elif score > 0:
        return "productive", "low"
    elif score == 0:
        return "neutral", "neutral"
    elif score > -25:
        return "unproductive", "low"
    else:
        return "unproductive", "high"

def update_enhanced_classification(activity, classification_data):
    """Update user config with enhanced classification data"""
    from .user_config import load_user_config
    import json
    import pathlib
    
    CONFIG_PATH = pathlib.Path(__file__).parent.parent / "data" / "user_config.json"
    
    config = load_user_config()
    config['custom_classifications'][activity] = classification_data
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"[FEEDBACK] Saved enhanced classification for '{activity}'")

if __name__ == "__main__":
    ask_for_feedback()
