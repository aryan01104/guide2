#!/usr/bin/env python3
"""
Activity pattern recognition and session grouping
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from ..database.operations import (
    get_db_session, get_recent_activities, save_activity_session,
    get_activity_patterns
)
from ..database.models import ActivityLog, ActivityPattern
from .flow_analysis import FlowAwareAnalyzer

class PatternRecognizer:
    """Recognizes patterns in activities and groups them into sessions"""
    
    def __init__(self, session_gap_minutes: int = 15):
        self.session_gap_minutes = session_gap_minutes
        self.confidence_threshold = 75  # Only auto-classify if >75% confident
        self.flow_analyzer = FlowAwareAnalyzer()
    
    def find_activity_groups(self, activities: List[ActivityLog]) -> List[List[ActivityLog]]:
        """Group activities into sessions based on time gaps"""
        if not activities:
            return []
        
        activities = sorted(activities, key=lambda x: x.timestamp_start)
        groups = []
        current_group = [activities[0]]
        
        for activity in activities[1:]:
            time_gap = (activity.timestamp_start - current_group[-1].timestamp_start).total_seconds() / 60
            
            if time_gap <= self.session_gap_minutes:
                current_group.append(activity)
            else:
                groups.append(current_group)
                current_group = [activity]
        
        groups.append(current_group)
        return groups
    
    def find_matching_pattern(self, features: Dict) -> Optional[ActivityPattern]:
        """Find existing pattern that matches current activities"""
        patterns = get_activity_patterns()
        
        best_match = None
        best_score = 0
        
        for pattern in patterns:
            pattern_apps = json.loads(pattern.apps)
            pattern_domains = json.loads(pattern.domains) if pattern.domains else []
            pattern_keywords = json.loads(pattern.keywords)
            
            # Calculate similarity score
            app_overlap = len(set(features['apps']) & set(pattern_apps))
            domain_overlap = len(set(features['domains']) & set(pattern_domains))
            keyword_overlap = len(set(features['keywords']) & set(pattern_keywords))
            
            # Weighted scoring
            total_pattern_features = len(pattern_apps) + len(pattern_domains) + len(pattern_keywords)
            if total_pattern_features > 0:
                score = (app_overlap * 3 + domain_overlap * 2 + keyword_overlap) / total_pattern_features
                
                if score > best_score and score > 0.3:  # At least 30% similarity
                    best_score = score
                    best_match = pattern
        
        return best_match
    
    def extract_features(self, activities: List[ActivityLog]) -> Dict:
        """Extract features from a group of activities"""
        apps = set()
        domains = set()
        keywords = set()
        
        for activity in activities:
            details = activity.details.lower()
            
            # Extract app names
            if '|' in activity.details:
                parts = activity.details.split('|')
                if len(parts) > 1:
                    app_or_title = parts[1].strip()
                    apps.add(app_or_title.split()[0] if app_or_title else "unknown")
            
            # Extract domains from URLs
            if 'http' in details:
                try:
                    start = details.find('http')
                    url_part = details[start:].split('|')[0] if '|' in details[start:] else details[start:]
                    if '://' in url_part:
                        domain = url_part.split('://')[1].split('/')[0]
                        domains.add(domain)
                except:
                    pass
            
            # Extract keywords
            words = details.replace('|', ' ').split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    keywords.add(word.lower())
        
        return {
            'apps': list(apps),
            'domains': list(domains), 
            'keywords': list(keywords),
            'total_duration': sum(a.duration_sec for a in activities),
            'activity_count': len(activities)
        }
    
    def classify_session_with_flow_analysis(self, activities: List[ActivityLog], 
                                          features: Dict) -> Tuple[str, str, int, Dict]:
        """Use flow-aware analysis to classify session"""
        
        # Use flow analyzer
        session_type, flow_stats = self.flow_analyzer.calculate_session_type_with_dominance(activities)
        session_name = self.flow_analyzer.generate_session_name(activities, session_type, flow_stats)
        flow_analysis = self.flow_analyzer.analyze_session_flow_quality(activities, flow_stats)
        
        # Calculate confidence based on flow analysis and dominance
        base_confidence = 50
        
        # Higher confidence for clear dominance
        if flow_stats.get('productive_ratio', 0) >= 0.75 or flow_stats.get('unproductive_ratio', 0) >= 0.75:
            base_confidence += 25
        elif flow_stats.get('productive_ratio', 0) >= 0.6 or flow_stats.get('unproductive_ratio', 0) >= 0.6:
            base_confidence += 15
        
        # Higher confidence for good flow quality
        flow_score = flow_analysis.get('flow_score', 50)
        if flow_score >= 80:
            base_confidence += 15
        elif flow_score >= 60:
            base_confidence += 10
        
        # Higher confidence for longer sessions
        duration_min = flow_stats.get('meaningful_time_sec', 0) // 60
        if duration_min >= 20:
            base_confidence += 10
        elif duration_min >= 10:
            base_confidence += 5
        
        # Lower confidence for mixed sessions
        if session_type in ['mixed', 'mostly_productive', 'mostly_unproductive']:
            base_confidence -= 15
        
        # Cap confidence
        confidence = min(95, max(30, base_confidence))
        
        # Map session types to standard format
        type_mapping = {
            'productive': 'productive',
            'mostly_productive': 'productive',
            'unproductive': 'unproductive', 
            'mostly_unproductive': 'unproductive',
            'mixed': 'unclear',
            'neutral': 'unclear'
        }
        
        standard_type = type_mapping.get(session_type, 'unclear')
        
        # Combine flow stats with additional metadata
        enhanced_stats = {
            **flow_stats,
            **flow_analysis,
            'classification_method': 'flow_aware',
            'original_session_type': session_type
        }
        
        return session_name, standard_type, confidence, enhanced_stats
    
    def analyze_recent_activities(self, hours_back: int = 2) -> List[Dict]:
        """Analyze recent activities and group into sessions"""
        
        activities = get_recent_activities(hours_back)
        
        if not activities:
            return []
        
        # Group activities into sessions
        activity_groups = self.find_activity_groups(activities)
        session_results = []
        
        for group in activity_groups:
            if len(group) == 1 and group[0].duration_sec < 60:
                continue  # Skip very short single activities
            
            features = self.extract_features(group)
            
            # Try to find matching pattern
            matching_pattern = self.find_matching_pattern(features)
            
            if matching_pattern and matching_pattern.success_rate > 70:
                # High confidence match - auto-classify
                session_name = matching_pattern.pattern_name
                session_type = matching_pattern.session_type
                confidence = min(95, matching_pattern.success_rate)
                
                # Save session
                start_time = min(a.timestamp_start for a in group)
                end_time = max(a.timestamp_start for a in group) + timedelta(seconds=max(a.duration_sec for a in group))
                total_duration = sum(a.duration_sec for a in group)
                
                # Calculate productivity score from activities
                session_score = self.calculate_session_productivity_score(group)
                
                session_id = save_activity_session(
                    session_name=session_name,
                    productivity_score=session_score,
                    start_time=start_time,
                    end_time=end_time,
                    total_duration_sec=total_duration,
                    user_confirmed=True
                )
                
                session_results.append({
                    'session_id': session_id,
                    'session_name': session_name,
                    'session_type': session_type,
                    'confidence': confidence,
                    'auto_classified': True,
                    'activities': group
                })
            else:
                # Use flow-aware classifier
                session_name, session_type, confidence, enhanced_stats = self.classify_session_with_flow_analysis(group, features)
                
                # Save session
                start_time = min(a.timestamp_start for a in group)
                end_time = max(a.timestamp_start for a in group) + timedelta(seconds=max(a.duration_sec for a in group))
                total_duration = sum(a.duration_sec for a in group)
                
                # Calculate productivity score from activities
                session_score = self.calculate_session_productivity_score(group)
                
                auto_classified = confidence >= self.confidence_threshold
                
                session_id = save_activity_session(
                    session_name=session_name,
                    productivity_score=session_score,
                    start_time=start_time,
                    end_time=end_time,
                    total_duration_sec=total_duration,
                    user_confirmed=auto_classified
                )
                
                session_results.append({
                    'session_id': session_id,
                    'session_name': session_name,
                    'session_type': session_type,
                    'confidence': confidence,
                    'auto_classified': auto_classified,
                    'activities': group,
                    'flow_stats': enhanced_stats
                })
        
        return session_results
    
    def calculate_session_productivity_score(self, activities):
        """Calculate time-weighted productivity score for a group of activities"""
        if not activities:
            return 0
        
        total_weighted_score = 0
        total_duration = 0
        
        for activity in activities:
            if activity.productivity_score is not None:
                duration = activity.duration_sec
                total_weighted_score += activity.productivity_score * duration
                total_duration += duration
        
        if total_duration == 0:
            return 0
        
        # Calculate weighted average
        avg_score = round(total_weighted_score / total_duration)
        
        return avg_score

def analyze_and_group_activities():
    """Main function to analyze recent activities"""
    recognizer = PatternRecognizer()
    results = recognizer.analyze_recent_activities(hours_back=2)
    
    print(f"[PATTERN] Analyzed {len(results)} sessions")
    for result in results:
        status = "AUTO" if result['auto_classified'] else "NEEDS REVIEW"
        print(f"  - {result['session_name']} ({result['confidence']}%) [{status}]")
    
    return results

if __name__ == "__main__":
    from ..database.operations import init_database
    init_database()
    analyze_and_group_activities()