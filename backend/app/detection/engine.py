"""
Detection Engine — Rule-based suspicious activity detection
"""
from typing import List, Dict, Any


DETECTION_RULES = [
    {
        "name": "brute_force_login",
        "description": "Multiple failed logins (potential brute force)",
        "event_type": "Failed Logon",
        "threshold": 5,
        "window_minutes": 10,
        "severity": "high",
        "confidence": 0.85,
    },
    {
        "name": "privilege_escalation",
        "description": "Special privileges assigned after logon",
        "event_type": "Special Privileges Assigned",
        "threshold": 1,
        "severity": "high",
        "confidence": 0.9,
    },
    {
        "name": "log_cleared",
        "description": "Audit log was cleared — potential cover-up",
        "event_type": "Audit Log Cleared",
        "threshold": 1,
        "severity": "critical",
        "confidence": 0.95,
    },
    {
        "name": "new_service_installed",
        "description": "New service installed — possible persistence mechanism",
        "event_type": "Service Installed",
        "threshold": 1,
        "severity": "high",
        "confidence": 0.8,
    },
    {
        "name": "account_created",
        "description": "New user account created",
        "event_type": "User Account Created",
        "threshold": 1,
        "severity": "medium",
        "confidence": 0.7,
    },
    {
        "name": "account_locked",
        "description": "User account locked out",
        "event_type": "Account Locked Out",
        "threshold": 1,
        "severity": "medium",
        "confidence": 0.75,
    },
    {
        "name": "scheduled_task_created",
        "description": "Scheduled task created — possible persistence",
        "event_type": "Scheduled Task Created",
        "threshold": 1,
        "severity": "medium",
        "confidence": 0.7,
    },
]


def run_detection(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run all detection rules against a list of normalized events.

    Returns:
        List of alerts generated.
    """
    alerts = []
    event_type_counts: Dict[str, List[Dict]] = {}

    for event in events:
        et = event.get("event_type", "")
        if et not in event_type_counts:
            event_type_counts[et] = []
        event_type_counts[et].append(event)

    for rule in DETECTION_RULES:
        matching = event_type_counts.get(rule["event_type"], [])
        if len(matching) >= rule["threshold"]:
            alerts.append({
                "rule_name": rule["name"],
                "title": rule["description"],
                "severity": rule["severity"],
                "confidence": rule["confidence"],
                "event_count": len(matching),
                "events": matching[:5],  # First 5 matching events
            })

    return alerts
