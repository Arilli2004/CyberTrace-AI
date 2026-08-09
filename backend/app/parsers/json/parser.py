"""
JSON Log Parser — CyberTrace AI
"""
import json
from typing import List, Dict, Any


def parse_json(file_path: str) -> List[Dict[str, Any]]:
    """Parse JSON / JSONL log files into normalized events."""
    events = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read().strip()

    # Try parsing as JSON array
    if content.startswith("[") and content.endswith("]"):
        try:
            records = json.loads(content)
            for r in records:
                if isinstance(r, dict):
                    events.append(_normalize_json_dict(r))
            return events
        except Exception:
            pass

    # Fallback to JSON Lines (JSONL)
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    events.append(_normalize_json_dict(data))
            except Exception:
                continue

    return events


def _normalize_json_dict(d: dict) -> Dict[str, Any]:
    lower_d = {str(k).lower(): v for k, v in d.items()}
    return {
        "timestamp": lower_d.get("timestamp") or lower_d.get("time") or lower_d.get("date") or "",
        "source": "JSON Log",
        "event_type": lower_d.get("event_type") or lower_d.get("action") or lower_d.get("event") or "JSON Event",
        "user": str(lower_d.get("user") or lower_d.get("username") or ""),
        "host": str(lower_d.get("host") or lower_d.get("hostname") or ""),
        "ip_address": str(lower_d.get("ip") or lower_d.get("ip_address") or lower_d.get("src_ip") or ""),
        "severity": str(lower_d.get("severity") or "low").lower(),
        "description": str(lower_d.get("description") or lower_d.get("message") or json.dumps(d)[:200]),
        "raw_data": d,
    }
