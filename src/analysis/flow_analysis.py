#!/usr/bin/env python3
"""
Legacy flow analysis module - imports from modularized components
"""

# Import everything from the new modular components for backward compatibility
from .activity_classifier import ActivityClassifier
from .batch_sessionizer import (GAP_THRESHOLD_SEC, MICRO_BREAK_THRESHOLD_SEC,
                                ActivityLogStub, batch_sessionize,
                                calculate_weighted_score, classify_type,
                                generate_session_name)
from .flow_analyzer import FlowAnalyzer

# Create aliases for backward compatibility
FlowAwareAnalyzer = ActivityClassifier  # Legacy name
gap_threshold_sec = GAP_THRESHOLD_SEC
micro_break_threshold_sec = MICRO_BREAK_THRESHOLD_SEC
weighted_score = calculate_weighted_score
session_name = generate_session_name
