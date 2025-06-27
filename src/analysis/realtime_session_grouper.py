#!/usr/bin/env python3
"""
Real-time session grouping based on context switches and natural workflow patterns
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from config.settings import REALTIME_SESSION_SETTINGS
from ..database.operations import save_activity_session
from ..database.models import ActivityLog
from .flow_analysis import FlowAwareAnalyzer

class RealTimeSessionGrouper:
    """Groups activities into sessions in real-time based on context switches"""
    
    def __init__(self):
        # Load configuration
        self.minimum_focus_time = REALTIME_SESSION_SETTINGS['minimum_focus_time_seconds']
        self.minimum_break_time = REALTIME_SESSION_SETTINGS['minimum_break_time_seconds']
        self.context_switch_threshold = REALTIME_SESSION_SETTINGS['context_switch_threshold_seconds']
        self.noise_threshold = REALTIME_SESSION_SETTINGS['noise_threshold_seconds']
        self.session_timeout = REALTIME_SESSION_SETTINGS['session_timeout_seconds']
        
        # Session state
        self.current_session = None
        self.current_context = None  # 'productive', 'unproductive', 'neutral'
        self.context_start_time = None
        self.pending_activities = []
        
        # Flow analyzer for activity classification
        self.flow_analyzer = FlowAwareAnalyzer()
    
    def on_new_activity(self, activity: ActivityLog):
        """Called every time a new activity is logged"""
        
        # 1. Skip noise activities
        if activity.duration_sec < self.noise_threshold:
            print(f"[REALTIME_SESSION] Ignoring noise activity: {activity.details} ({activity.duration_sec}s)")
            return
        
        # 2. Get activity classification
        activity_type = self.classify_activity(activity)
        print(f"[REALTIME_SESSION] Activity: {activity.details} classified as: {activity_type}")
        
        # 3. Determine if context switch occurred
        if self.current_context is None:
            # First activity - start new session
            print(f"[REALTIME_SESSION] Starting first session with {activity_type} activity")
            self.start_new_session(activity, activity_type)
            
        elif activity_type != self.current_context:
            # Different context - check if we should switch
            time_in_current_context = (activity.timestamp_start - self.context_start_time).total_seconds()
            
            print(f"[REALTIME_SESSION] Context switch detected: {self.current_context} -> {activity_type}")
            print(f"[REALTIME_SESSION] Time in current context: {time_in_current_context}s")
            
            if self.should_create_session(time_in_current_context, activity_type):
                # End current session and start new one
                print(f"[REALTIME_SESSION] Creating session boundary")
                self.finalize_current_session()
                self.start_new_session(activity, activity_type)
            else:
                # Too brief - might be temporary distraction
                print(f"[REALTIME_SESSION] Adding to pending activities (too brief for context switch)")
                self.pending_activities.append(activity)
                
        else:
            # Same context - continue current session
            print(f"[REALTIME_SESSION] Continuing {activity_type} session")
            self.add_to_current_session(activity)
        
        # 4. Check for session timeout
        self.check_session_timeout()
    
    def classify_activity(self, activity: ActivityLog) -> str:
        """Classify individual activity type"""
        return self.flow_analyzer.classify_activity_type(activity)
    
    def should_create_session(self, time_in_context: float, new_activity_type: str) -> bool:
        """Decide if we should end current session and start new one"""
        
        if self.current_context == 'productive':
            # End productive session if we've been focused for minimum time
            # and switching to unproductive
            if (time_in_context >= self.minimum_focus_time and 
                new_activity_type == 'unproductive'):
                print(f"[REALTIME_SESSION] Productive focus time met ({time_in_context}s >= {self.minimum_focus_time}s), switching to break")
                return True
                
        elif self.current_context == 'unproductive':
            # End break session if we've been breaking for minimum time
            # and switching to productive
            if (time_in_context >= self.minimum_break_time and 
                new_activity_type == 'productive'):
                print(f"[REALTIME_SESSION] Break time met ({time_in_context}s >= {self.minimum_break_time}s), switching to work")
                return True
                
        # Always end session if context switch is major (5+ minutes)
        if time_in_context >= self.context_switch_threshold:
            print(f"[REALTIME_SESSION] Context switch threshold met ({time_in_context}s >= {self.context_switch_threshold}s)")
            return True
            
        return False
    
    def start_new_session(self, activity: ActivityLog, activity_type: str):
        """Start a new activity session"""
        self.current_session = {
            'activities': [activity],
            'start_time': activity.timestamp_start,
            'dominant_type': activity_type
        }
        self.current_context = activity_type
        self.context_start_time = activity.timestamp_start
        
        # Add any pending activities if they match new context
        matching_pending = [a for a in self.pending_activities 
                          if self.classify_activity(a) == activity_type]
        
        if matching_pending:
            print(f"[REALTIME_SESSION] Adding {len(matching_pending)} pending activities to new session")
            self.current_session['activities'].extend(matching_pending)
            # Remove matched activities from pending
            self.pending_activities = [a for a in self.pending_activities 
                                     if self.classify_activity(a) != activity_type]
        
        print(f"[REALTIME_SESSION] Started new {activity_type} session")
    
    def add_to_current_session(self, activity: ActivityLog):
        """Add activity to current session"""
        if self.current_session:
            self.current_session['activities'].append(activity)
    
    def finalize_current_session(self):
        """Complete current session and save to database"""
        if not self.current_session:
            return
        
        session = self.current_session
        activities = session['activities']
        
        # Calculate session metrics
        total_duration = sum(a.duration_sec for a in activities)
        session_name = self.generate_session_name(activities, session['dominant_type'])
        
        # Calculate end time from last activity
        end_time = activities[-1].timestamp_start + timedelta(seconds=activities[-1].duration_sec)
        
        # Calculate time-weighted productivity score
        session_score = self.calculate_session_score(activities)
        
        # Save to database
        try:
            save_activity_session(
                session_name=session_name,
                productivity_score=session_score,
                start_time=session['start_time'],
                end_time=end_time,
                total_duration_sec=total_duration,
                user_confirmed=False  # Sessions scores are mathematical, not user-confirmed
            )
            
            print(f"[REALTIME_SESSION] ✅ Created session: '{session_name}' (score: {session_score}, {total_duration//60}min, {len(activities)} activities)")
            
        except Exception as e:
            print(f"[REALTIME_SESSION] ❌ Error saving session: {e}")
        
        # Clear current session
        self.current_session = None
        self.current_context = None
        self.context_start_time = None
    
    def calculate_session_score(self, activities: List[ActivityLog]) -> int:
        """Calculate time-weighted productivity score for session"""
        if not activities:
            return 0
        
        total_weighted_score = 0
        total_duration = 0
        
        for activity in activities:
            duration = activity.duration_sec
            
            # Get productivity score from activity (will be None if not yet classified)
            productivity_score = getattr(activity, 'productivity_score', None)
            
            # If not classified yet, use default neutral value
            if productivity_score is None:
                productivity_score = 0  # Neutral
            
            # Weight by duration
            total_weighted_score += productivity_score * duration
            total_duration += duration
        
        if total_duration == 0:
            return 0
        
        # Calculate weighted average
        avg_score = round(total_weighted_score / total_duration)
        
        return avg_score
    
    def generate_session_name(self, activities: List[ActivityLog], dominant_type: str) -> str:
        """Generate descriptive session name based on activities"""
        if not activities:
            return "Empty Session"
        
        # Extract key features
        apps = set()
        domains = set()
        
        for activity in activities:
            details = activity.details.lower()
            
            # Extract app names (before the | separator)
            if '|' in activity.details:
                app_part = activity.details.split('|')[0].strip()
                if app_part:
                    apps.add(app_part)
            
            # Extract domains for browser activities
            if 'http' in details:
                try:
                    # Simple domain extraction
                    if '://' in details:
                        url_part = details.split('://')[1].split('/')[0]
                        domain = url_part.replace('www.', '')
                        domains.add(domain)
                except:
                    pass
        
        # Generate name based on patterns
        duration_min = sum(a.duration_sec for a in activities) // 60
        
        # Development patterns
        if any('code' in app.lower() or 'terminal' in app.lower() for app in apps):
            if any('localhost' in d for d in domains):
                return f"Web Development Session"
            else:
                return f"Coding Session"
        
        # Research patterns
        if any(d in domains for d in ['stackoverflow.com', 'github.com']):
            return f"Technical Research"
        
        # Entertainment patterns  
        if any(d in domains for d in ['youtube.com', 'netflix.com', 'x.com', 'twitter.com']):
            if dominant_type == 'unproductive':
                return f"Entertainment Break"
            else:
                return f"Mixed Media Session"
        
        # Generic patterns based on type
        if dominant_type == 'productive':
            return f"Productive Work Session"
        elif dominant_type == 'unproductive':
            return f"Break Session"
        else:
            return f"Mixed Activity Session"
    
    def check_session_timeout(self):
        """Check if current session has timed out due to inactivity"""
        if not self.current_session:
            return
        
        last_activity = self.current_session['activities'][-1]
        last_activity_end = last_activity.timestamp_start + timedelta(seconds=last_activity.duration_sec)
        time_since_last = datetime.now() - last_activity_end
        
        if time_since_last.total_seconds() > self.session_timeout:
            print(f"[REALTIME_SESSION] Session timeout after {time_since_last} of inactivity")
            self.finalize_current_session()
    
    def force_finalize_session(self):
        """Manually finalize current session (useful for shutdown)"""
        if self.current_session:
            print("[REALTIME_SESSION] Force finalizing current session")
            self.finalize_current_session()