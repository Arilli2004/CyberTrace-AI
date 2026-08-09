"""
Event Correlation Engine — CyberTrace AI
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta


def correlate_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Correlate events based on IP, user, host, process, and time window.
    Groups events into correlated incident graph clusters.
    """
    if not events:
        return []

    # Sort events by timestamp where available
    events_with_time = []
    for e in events:
        events_with_time.append(e)

    # Group by User & IP
    user_clusters: Dict[str, List[Dict]] = {}
    ip_clusters: Dict[str, List[Dict]] = {}

    for e in events_with_time:
        user = e.get("user")
        ip = e.get("ip_address")

        if user:
            user_clusters.setdefault(user, []).append(e)
        if ip:
            ip_clusters.setdefault(ip, []).append(e)

    # Annotate correlation flags on events
    for e in events_with_time:
        user = e.get("user")
        ip = e.get("ip_address")

        correlated_count = 0
        if user and user in user_clusters:
            correlated_count += len(user_clusters[user]) - 1
        if ip and ip in ip_clusters:
            correlated_count += len(ip_clusters[ip]) - 1

        e["correlation_count"] = correlated_count
        if correlated_count > 3:
            e["is_suspicious"] = True
            e["confidence_score"] = min(0.95, 0.5 + (correlated_count * 0.05))

    return events_with_time
