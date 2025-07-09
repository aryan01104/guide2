#!/usr/bin/env python3
"""
Flow state analysis for productivity sessions
"""

from typing import Dict, List, Tuple

from .activity_classifier import ActivityClassifier


class FlowAnalyzer:
    """
    Analyzes flow quality and context switching patterns in activity sessions
    """

    def __init__(self):
        self.classifier = ActivityClassifier()

    def filter_noise_activities(self, activities: List) -> Tuple[List, List]:
        """Separate meaningful activities from noise based on duration"""
        meaningful = []
        noise = []

        for activity in activities:
            if activity.duration_sec >= self.classifier.secs4flow:
                meaningful.append(activity)
            else:
                noise.append(activity)

        return meaningful, noise

    def calculate_session_type_with_dominance(
        self, activities: List
    ) -> Tuple[str, Dict]:
        """Calculate session type using dominance ratio and noise filtering"""
        if not activities:
            return "neutral", {}

        meaningful_activities, noise_activities = self.filter_noise_activities(
            activities
        )

        total_time = sum(a.duration_sec for a in activities)
        meaningful_time = sum(a.duration_sec for a in meaningful_activities)
        noise_time = sum(a.duration_sec for a in noise_activities)

        productive_time = 0
        unproductive_time = 0
        neutral_time = 0

        for activity in meaningful_activities:
            if activity.productivity_score > 0:
                productive_time += activity.duration_sec
            elif activity.productivity_score < 0:
                unproductive_time += activity.duration_sec
            else:
                neutral_time += activity.duration_sec

        if meaningful_time > 0:
            productive_ratio = productive_time / meaningful_time
            unproductive_ratio = unproductive_time / meaningful_time
            neutral_ratio = neutral_time / meaningful_time
        else:
            productive_ratio = unproductive_ratio = neutral_ratio = 0

        if productive_ratio >= self.classifier.dominance_ratio:
            session_type = "productive"
        elif unproductive_ratio >= self.classifier.dominance_ratio:
            session_type = "unproductive"
        elif productive_ratio > unproductive_ratio:
            session_type = "mostly_productive"
        elif unproductive_ratio > productive_ratio:
            session_type = "mostly_unproductive"
        else:
            session_type = "mixed"

        stats = {
            "total_time_sec": total_time,
            "meaningful_time_sec": meaningful_time,
            "noise_time_sec": noise_time,
            "productive_time_sec": productive_time,
            "unproductive_time_sec": unproductive_time,
            "neutral_time_sec": neutral_time,
            "productive_ratio": round(productive_ratio, 3),
            "unproductive_ratio": round(unproductive_ratio, 3),
            "neutral_ratio": round(neutral_ratio, 3),
            "noise_ratio": round(noise_time / total_time if total_time > 0 else 0, 3),
            "meaningful_activity_count": len(meaningful_activities),
            "noise_activity_count": len(noise_activities),
        }

        return session_type, stats

    def analyze_session_flow_quality(self, activities: List, stats: Dict) -> Dict:
        """Analyze the flow quality of a session based on switching patterns"""
        meaningful_activities, noise_activities = self.filter_noise_activities(
            activities
        )

        if len(meaningful_activities) < 2:
            return {"flow_quality": "single_task", "switches": 0, "flow_score": 100}

        switches = 0
        current_type = self.classifier.classify_activity_type(meaningful_activities[0])

        for activity in meaningful_activities[1:]:
            activity_type = self.classifier.classify_activity_type(activity)
            if activity_type != current_type:
                switches += 1
                current_type = activity_type

        session_duration_min = stats["meaningful_time_sec"] / 60
        switches_per_hour = (
            (switches / session_duration_min * 60) if session_duration_min > 0 else 0
        )

        if switches_per_hour <= 2:
            flow_quality = "excellent"
            flow_score = 90 + min(10, (2 - switches_per_hour) * 5)
        elif switches_per_hour <= 5:
            flow_quality = "good"
            flow_score = 70 + (5 - switches_per_hour) * 6
        elif switches_per_hour <= 10:
            flow_quality = "moderate"
            flow_score = 40 + (10 - switches_per_hour) * 6
        else:
            flow_quality = "fragmented"
            flow_score = max(10, 40 - (switches_per_hour - 10) * 3)

        return {
            "flow_quality": flow_quality,
            "switches": switches,
            "switches_per_hour": round(switches_per_hour, 1),
            "flow_score": round(flow_score, 1),
            "noise_activities": len(noise_activities),
        }

    def generate_session_name(
        self, activities: List, session_type: str, stats: Dict
    ) -> str:
        """Generate descriptive session name based on activities and patterns"""
        if not activities:
            return "Empty Session"

        apps = set()
        domains = set()

        meaningful_activities, _ = self.filter_noise_activities(activities)

        for activity in meaningful_activities:
            details = activity.details.lower()
            if "|" in activity.details:
                parts = activity.details.split("|")
                if len(parts) > 1:
                    app_or_title = parts[1].strip()
                    if app_or_title:
                        apps.add(app_or_title.split()[0])
            if "http" in details:
                try:
                    start = details.find("http")
                    url_part = (
                        details[start:].split("|")[0]
                        if "|" in details[start:]
                        else details[start:]
                    )
                    if "://" in url_part:
                        domain = url_part.split("://")[1].split("/")[0]
                        domains.add(domain.replace("www.", ""))
                except:
                    pass

        duration_min = stats["meaningful_time_sec"] // 60

        if "code" in " ".join(apps).lower() or "terminal" in " ".join(apps).lower():
            if any("localhost" in d for d in domains):
                return f"Web Development Session"
            else:
                return f"Coding Session"
        if any(
            d in domains
            for d in ["stackoverflow.com", "github.com", "docs.", "documentation"]
        ):
            return f"Technical Research"
        if any(
            d in domains for d in ["youtube.com", "netflix.com", "x.com", "twitter.com"]
        ):
            if session_type == "unproductive":
                return f"Entertainment Break"
            else:
                return f"Mixed Media Session"
        if session_type == "productive":
            return f"Productive Work Session"
        elif session_type == "unproductive":
            return f"Break Time"
        else:
            return f"Mixed Activity Session"
