import csv
import json
from .user_config import load_user_config, update_custom_classification
from .llm_client import chat

def classify_activities(rows):
    config = load_user_config()
    print(f"[CLASSIFIER] Starting classification for {len(rows)} activities.")
    results = []
    unknowns = []

    for r in rows:
        det = r["details"]
        user_cls = config["custom_classifications"].get(det)
        if user_cls:
            category = user_cls
            print(f"[CLASSIFIER] Used custom classification for '{det}': {category}")
        else:
            system_prompt = f"""You are an expert productivity analyst. Classify activities using this framework:

PRODUCTIVE: Activities that directly advance the user's main goal or professional development
- Main goal: {config['main_goal']}
- Profession: {config['profession']}
- Side aims: {config['side_aims']}
- Examples: coding, writing, research, client meetings, skill learning

UNPRODUCTIVE: Entertainment, distraction, or time-wasting activities
- Examples: social media browsing, random YouTube, gaming (unless game dev)
- Known break activities: {config['break_activities']}

NEUTRAL: Necessary but non-goal-advancing tasks
- Examples: email management, admin tasks, legitimate breaks

RESPOND WITH VALID JSON ONLY:
{{"classification": "productive|unproductive|neutral", "confidence": 0-100, "reasoning": "brief explanation"}}

Examples:
- "VSCode | editing main.py" → {{"classification": "productive", "confidence": 95, "reasoning": "Direct coding work"}}
- "YouTube | random videos" → {{"classification": "unproductive", "confidence": 90, "reasoning": "Entertainment distraction"}}
- "Gmail | inbox management" → {{"classification": "neutral", "confidence": 80, "reasoning": "Necessary admin task"}}"""

            user_prompt = f"Classify this activity: {det}"
            resp = chat([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0)
            
            # Parse JSON response safely
            try:
                result = json.loads(resp.choices[0].message.content.strip())
                category = result['classification']
                confidence = result.get('confidence', 50)
                reasoning = result.get('reasoning', 'No reasoning provided')
                
                # Add to unknowns if confidence is low
                if confidence < 75:
                    unknowns.append(det)
                    
                print(f"[CLASSIFIER] Activity: '{det}' classified as: {category} (confidence: {confidence}%, reasoning: {reasoning})")
                
            except (json.JSONDecodeError, KeyError) as e:
                # Fallback for malformed responses
                category = 'neutral'
                confidence = 30
                print(f"[CLASSIFIER] Failed to parse LLM response for '{det}': {e}. Using neutral classification.")
                unknowns.append(det)
        r["category"] = category
        results.append(r)
    return results, unknowns

def write_classified_log(rows, path):
    if not rows: return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[CLASSIFIER] Wrote classified activity log to: {path}")
