#!/usr/bin/env python3
"""
Flow-aware activity analysis based on research principles
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json

from ..database.models import ActivityLog
from ..user_config import load_user_config
from ..llm_client import chat

class FlowAwareAnalyzer:
    """
    Analyzes activity sessions using flow state research principles
    """
    
    def __init__(self):
        # Research-based thresholds
        self.noise_threshold_seconds = 120  # 2 minutes - ignore brief activities
        self.dominance_ratio = 0.75  # 75% rule for session classification
        self.consecutive_time_required = 180  # 3 minutes to indicate real context switch
        self.flow_break_threshold = 180  # 3+ minutes breaks flow state
        
        # Activity type mappings
        self.productivity_keywords = {
            'productive': ['localhost', 'github', 'stackoverflow', 'documentation', 'vscode', 'terminal', 'python', 'code'],
            'unproductive': ['youtube', 'facebook', 'instagram', 'tiktok', 'netflix', 'gaming', 'memes', 'twitter', 'x.com'],
            'neutral': ['email', 'calendar', 'news', 'google', 'search']
        }
    
    def classify_activity_type(self, activity: ActivityLog) -> str:
        """Classify individual activity using smart LLM classification"""
        
        # Use existing score if available and user-confirmed
        if hasattr(activity, 'productivity_score') and activity.productivity_score is not None and hasattr(activity, 'user_confirmed') and activity.user_confirmed:
            # Convert score to category for backward compatibility
            if activity.productivity_score >= 15:
                return 'productive'
            elif activity.productivity_score <= -15:
                return 'unproductive'
            else:
                return 'neutral'
        
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
            custom_classifications = config.get('custom_classifications', {})
            if custom_classifications:
                user_examples = "\n\nUSER'S PERSONAL CLASSIFICATION PATTERNS (follow these closely):\n"
                for activity, data in custom_classifications.items():
                    if isinstance(data, dict) and 'productivity_score' in data:
                        score = data['productivity_score']
                        classification = data['classification']
                        intensity = data.get('intensity', '')
                        user_examples += f"- '{activity}' → {classification} (score: {score}, {intensity} intensity)\n"
                    elif isinstance(data, str):
                        # Legacy format
                        user_examples += f"- '{activity}' → {data}\n"
                
                user_examples += "\nFor similar activities, follow the user's established patterns and scoring preferences."
                system_prompt = base_prompt + user_examples
            else:
                system_prompt = base_prompt

            system_prompt += """

RESPOND WITH VALID JSON ONLY:
{{"productivity_score": -50 to +50, "confidence": 0-100, "reasoning": "brief explanation"}}

Examples:
- "VSCode | editing main.py" → {{"productivity_score": 45, "confidence": 95, "reasoning": "Direct coding work advancing main goals"}}
- "YouTube | random videos" → {{"productivity_score": -30, "confidence": 90, "reasoning": "Entertainment distraction during work time"}}
- "Gmail | inbox management" → {{"productivity_score": 5, "confidence": 80, "reasoning": "Necessary but light administrative task"}}"""

            user_prompt = f"Rate this activity: {activity.details}"
            resp = chat([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0)
            
            # Parse JSON response safely
            result = json.loads(resp.choices[0].message.content.strip())
            productivity_score = result['productivity_score']
            confidence = result.get('confidence', 50)
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            # Store scores in activity object
            if hasattr(activity, 'productivity_score'):
                activity.productivity_score = productivity_score
            if hasattr(activity, 'confidence_score'):
                activity.confidence_score = confidence
            if hasattr(activity, 'classification_text'):
                activity.classification_text = reasoning
            
            # Convert numerical score to categorical for backward compatibility
            if productivity_score >= 15:
                return 'productive'
            elif productivity_score <= -15:
                return 'unproductive'
            else:
                return 'neutral'
            
        except Exception as e:
            # Fallback to keyword-based classification if LLM fails
            print(f"[FLOW_ANALYZER] LLM classification failed for '{activity.details}': {e}. Using keyword fallback.")
            
            details_lower = activity.details.lower()
            for activity_type, keywords in self.productivity_keywords.items():
                if any(keyword in details_lower for keyword in keywords):
                    return activity_type
            return 'neutral'
    
    def filter_noise_activities(self, activities: List[ActivityLog]) -> Tuple[List[ActivityLog], List[ActivityLog]]:
        """
        Separate meaningful activities from noise based on duration
        Returns: (meaningful_activities, noise_activities)
        """
        meaningful = []
        noise = []
        
        for activity in activities:
            if activity.duration_sec >= self.noise_threshold_seconds:
                meaningful.append(activity)
            else:
                noise.append(activity)
        
        return meaningful, noise
    
    def calculate_session_type_with_dominance(self, activities: List[ActivityLog]) -> Tuple[str, Dict]:
        """
        Calculate session type using dominance ratio and noise filtering
        Returns: (session_type, stats_dict)
        """
        if not activities:
            return 'neutral', {}
        
        # Separate meaningful activities from noise
        meaningful_activities, noise_activities = self.filter_noise_activities(activities)
        
        # Calculate time distributions
        total_time = sum(a.duration_sec for a in activities)
        meaningful_time = sum(a.duration_sec for a in meaningful_activities)
        noise_time = sum(a.duration_sec for a in noise_activities)
        
        # Classify meaningful activities
        productive_time = 0
        unproductive_time = 0
        neutral_time = 0
        
        for activity in meaningful_activities:
            activity_type = self.classify_activity_type(activity)
            if activity_type == 'productive':
                productive_time += activity.duration_sec
            elif activity_type == 'unproductive':
                unproductive_time += activity.duration_sec
            else:
                neutral_time += activity.duration_sec
        
        # Calculate ratios (exclude noise from classification)
        if meaningful_time > 0:
            productive_ratio = productive_time / meaningful_time
            unproductive_ratio = unproductive_time / meaningful_time
            neutral_ratio = neutral_time / meaningful_time
        else:
            productive_ratio = unproductive_ratio = neutral_ratio = 0
        
        # Apply dominance rule
        if productive_ratio >= self.dominance_ratio:
            session_type = 'productive'
        elif unproductive_ratio >= self.dominance_ratio:
            session_type = 'unproductive'
        elif productive_ratio > unproductive_ratio:
            session_type = 'mostly_productive'
        elif unproductive_ratio > productive_ratio:
            session_type = 'mostly_unproductive'
        else:
            session_type = 'mixed'
        
        stats = {
            'total_time_sec': total_time,
            'meaningful_time_sec': meaningful_time,
            'noise_time_sec': noise_time,
            'productive_time_sec': productive_time,
            'unproductive_time_sec': unproductive_time,
            'neutral_time_sec': neutral_time,
            'productive_ratio': round(productive_ratio, 3),
            'unproductive_ratio': round(unproductive_ratio, 3),
            'neutral_ratio': round(neutral_ratio, 3),
            'noise_ratio': round(noise_time / total_time if total_time > 0 else 0, 3),
            'meaningful_activity_count': len(meaningful_activities),
            'noise_activity_count': len(noise_activities)
        }
        
        return session_type, stats
    
    def analyze_session_flow_quality(self, activities: List[ActivityLog], stats: Dict) -> Dict:
        """Analyze the flow quality of a session based on switching patterns"""
        meaningful_activities, noise_activities = self.filter_noise_activities(activities)
        
        if len(meaningful_activities) < 2:
            return {'flow_quality': 'single_task', 'switches': 0, 'flow_score': 100}
        
        # Count context switches
        switches = 0
        current_type = self.classify_activity_type(meaningful_activities[0])
        
        for activity in meaningful_activities[1:]:
            activity_type = self.classify_activity_type(activity)
            if activity_type != current_type:
                switches += 1
                current_type = activity_type
        
        # Calculate flow score (fewer switches = better flow)
        session_duration_min = stats['meaningful_time_sec'] / 60
        switches_per_hour = (switches / session_duration_min * 60) if session_duration_min > 0 else 0
        
        # Flow quality assessment
        if switches_per_hour <= 2:
            flow_quality = 'excellent'
            flow_score = 90 + min(10, (2 - switches_per_hour) * 5)
        elif switches_per_hour <= 5:
            flow_quality = 'good'
            flow_score = 70 + (5 - switches_per_hour) * 6
        elif switches_per_hour <= 10:
            flow_quality = 'moderate'
            flow_score = 40 + (10 - switches_per_hour) * 6
        else:
            flow_quality = 'fragmented'
            flow_score = max(10, 40 - (switches_per_hour - 10) * 3)
        
        return {
            'flow_quality': flow_quality,
            'switches': switches,
            'switches_per_hour': round(switches_per_hour, 1),
            'flow_score': round(flow_score, 1),
            'noise_activities': len(noise_activities)
        }
    
    def generate_session_name(self, activities: List[ActivityLog], session_type: str, stats: Dict) -> str:
        """Generate descriptive session name based on activities and patterns"""
        if not activities:
            return "Empty Session"
        
        # Extract key features
        apps = set()
        domains = set()
        
        meaningful_activities, _ = self.filter_noise_activities(activities)
        
        for activity in meaningful_activities:
            details = activity.details.lower()
            
            # Extract app names
            if '|' in activity.details:
                parts = activity.details.split('|')
                if len(parts) > 1:
                    app_or_title = parts[1].strip()
                    if app_or_title:
                        apps.add(app_or_title.split()[0])
            
            # Extract domains
            if 'http' in details:
                try:
                    start = details.find('http')
                    url_part = details[start:].split('|')[0] if '|' in details[start:] else details[start:]
                    if '://' in url_part:
                        domain = url_part.split('://')[1].split('/')[0]
                        domains.add(domain.replace('www.', ''))
                except:
                    pass
        
        # Generate name based on patterns
        duration_min = stats['meaningful_time_sec'] // 60
        
        # Development patterns
        if 'code' in ' '.join(apps).lower() or 'terminal' in ' '.join(apps).lower():
            if any('localhost' in d for d in domains):
                return f"Web Development Session"
            else:
                return f"Coding Session"
        
        # Research patterns
        if any(d in domains for d in ['stackoverflow.com', 'github.com', 'docs.', 'documentation']):
            return f"Technical Research"
        
        # Entertainment patterns
        if any(d in domains for d in ['youtube.com', 'netflix.com', 'x.com', 'twitter.com']):
            if session_type == 'unproductive':
                return f"Entertainment Break"
            else:
                return f"Mixed Media Session"
        
        # Work patterns
        if session_type == 'productive':
            return f"Productive Work Session"
        elif session_type == 'unproductive':
            return f"Break Time"
        else:
            return f"Mixed Activity Session"