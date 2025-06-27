#!/usr/bin/env python3
"""
Database models using SQLAlchemy
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey  
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ActivityLog(Base):
    """Activity log entry model"""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("activity_sessions.id"), nullable=True, index=True)
    timestamp_start = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # app_session or browser_tab_session
    details = Column(Text, nullable=False)
    duration_sec = Column(Integer, nullable=False)
    productivity_score = Column(Integer, nullable=True)  # -50 to +50 productivity score
    confidence_score = Column(Integer, nullable=True)  # 0-100 confidence in classification
    classification_text = Column(Text, nullable=True)  # Full LLM classification response with reasoning
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, event={self.event_type}, duration={self.duration_sec}s)>"

class UserConfig(Base):
    """User configuration model"""
    __tablename__ = "user_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CustomClassification(Base):
    """Custom activity classifications"""
    __tablename__ = "custom_classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    activity_details = Column(Text, nullable=False, unique=True)
    classification = Column(String(50), nullable=False)  # productive, unproductive, unclear
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivitySession(Base):
    """Grouped activity sessions based on patterns"""
    __tablename__ = "activity_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(200), nullable=False)  # "Web Development", "Entertainment Break"
    productivity_score = Column(Integer, nullable=True)  # -50 to +50 time-weighted average of activities
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    total_duration_sec = Column(Integer, nullable=False)
    user_confirmed = Column(Boolean, default=False)  # User approved this score
    created_at = Column(DateTime, default=datetime.utcnow)

class ActivityPattern(Base):
    """Learned patterns for activity recognition"""
    __tablename__ = "activity_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String(200), nullable=False)  # "Web Development"
    session_type = Column(String(50), nullable=False)   # productive, unproductive, unclear
    keywords = Column(Text, nullable=False)  # JSON array of keywords
    apps = Column(Text, nullable=False)      # JSON array of apps
    domains = Column(Text, nullable=True)    # JSON array of domains
    usage_count = Column(Integer, default=1)
    success_rate = Column(Integer, default=100)  # % of times user confirmed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)