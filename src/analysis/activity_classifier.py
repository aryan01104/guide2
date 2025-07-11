#!/usr/bin/env python3
"""
AI-powered activity classification using LLM
"""

import json
from typing import Dict, Optional

from ..llm_client import chat
from ..user_config import load_user_config


class ActivityClassifier:
    """
    Analyzes activity sessions using flow state research principles
    """

    def __init__(self):
        # Research-based thresholds
        self.dominance_ratio = 0.75  # 75% rule for session classification
        self.secs4flow = 15 * 60
        self.secs4break = 240

    def classify_activity_type(self, activity) -> str:
        """Classify individual activity using smart LLM classification"""
        # Use existing score if available and user-confirmed
        if (  # the activity has a productivity score and is user_confirmed
            hasattr(activity, "productivity_score")
            and activity.productivity_score is not None
            and hasattr(activity, "user_confirmed")
            and activity.user_confirmed
        ):
            # Convert score to category for backward compatibility
            if activity.productivity_score >= 15:
                return "productive"
            elif activity.productivity_score <= -15:
                return "unproductive"
            else:
                return "neutral"

        # Use smart LLM classification
        try:
            config = load_user_config()

            # Build personalized prompt with user's own examples
            base_prompt = f"""You are an expert productivity analyst. Rate activities using this scoring system:

PRODUCTIVITY SCORING (-50 to +50):
+40 to +50: Highly productive - Direct advancement of main goals, deep work, major progress
+20 to +39: Moderately productive - Professional development, skill building, meaningful work
+1 to +19: Slightly productive - Necessary tasks, light maintenance work
0: Neutral - Breaks, admin tasks, neither helping nor hurting goals
-1 to -19: Slightly unproductive - Minor distractions, procrastination
-20 to -39: Moderately unproductive - Social media, entertainment during work time
-40 to -50: Highly unproductive - Major time-wasting, activities that actively hurt goals

USER CONTEXT:
- Main goal: {config['main_goal']}
- Profession: {config['profession']}
- Side aims: {config['side_aims']}
- Known break activities: {config['break_activities']}"""

            # Add user's personal examples if available
            custom_classifications = config.get("custom_classifications", {})
            if custom_classifications:
                user_examples = "\n\nUSER'S PERSONAL CLASSIFICATION PATTERNS (follow these closely):\n"
                for activity_text, data in custom_classifications.items():
                    if isinstance(data, dict) and "productivity_score" in data:
                        score = data["productivity_score"]
                        classification = data["classification"]
                        intensity = data.get("intensity", "")
                        user_examples += f"- '{activity_text}' → {classification} (score: {score}, {intensity} intensity)\n"
                    elif isinstance(data, str):
                        # Legacy format
                        user_examples += f"- '{activity_text}' → {data}\n"
                user_examples += "\nFor similar activities, follow the user's established patterns and scoring preferences."
                system_prompt = base_prompt + user_examples
            else:
                system_prompt = base_prompt

            system_prompt += """

RESPOND WITH VALID JSON ONLY:
{"productivity_score": -50 to +50, "confidence": 0-100, "reasoning": "brief explanation"}

Examples:
- "VSCode | editing main.py" → {"productivity_score": 45, "confidence": 95, "reasoning": "Direct coding work advancing main goals"}
- "YouTube | random videos" → {"productivity_score": -30, "confidence": 90, "reasoning": "Entertainment distraction during work time"}
- "Gmail | inbox management" → {"productivity_score": 5, "confidence": 80, "reasoning": "Necessary but light administrative task"}"""

            user_prompt = f"Rate this activity: {activity.details}"
            resp = chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )

            # Parse JSON response safely
            result = json.loads(resp.choices[0].message.content.strip())
            productivity_score = result["productivity_score"]
            confidence = result.get("confidence", 50)
            reasoning = result.get("reasoning", "No reasoning provided")

            # Store scores in activity object
            if hasattr(activity, "productivity_score"):
                activity.productivity_score = productivity_score
            if hasattr(activity, "confidence_score"):
                activity.confidence_score = confidence
            if hasattr(activity, "classification_text"):
                activity.classification_text = reasoning

            # Convert numerical score to categorical for backward compatibility
            if productivity_score >= 15:
                return "productive"
            elif productivity_score <= -15:
                return "unproductive"
            else:
                return "neutral"

        except Exception as e:
            # Fallback to keyword-based classification if LLM fails
            print(
                f"[ACTIVITY_CLASSIFIER] LLM classification failed for '{activity.details}': {e}. Using keyword fallback."
            )
            return self._fallback_classification(activity)

    def _fallback_classification(self, activity) -> str:
        """Fallback keyword-based classification"""
        details_lower = activity.details.lower()
        for activity_type, keywords in self.productivity_keywords.items():
            if any(keyword in details_lower for keyword in keywords):
                return activity_type
        return "neutral"
