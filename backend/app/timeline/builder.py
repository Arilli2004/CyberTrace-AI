"""
Timeline Reconstruction Builder — CyberTrace AI
"""
from typing import List, Dict, Any
from datetime import datetime


def build_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Reconstruct chronological attack timeline from normalized events.
    """
    def parse_time(e):
        ts = e.get("timestamp")
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str) and ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass
        return datetime.min

    sorted_events = sorted(events, key=parse_time)
    
    # Assign sequence numbers
    for idx, e in enumerate(sorted_events, start=1):
        e["sequence_id"] = idx

    return sorted_events
