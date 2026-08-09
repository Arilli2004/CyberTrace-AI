"""
CSV Parser — Parse CSV log files
"""
import csv
from typing import List, Dict, Any
from pathlib import Path


COMMON_TIMESTAMP_FIELDS = ["timestamp", "time", "datetime", "date", "log_time", "event_time"]
COMMON_USER_FIELDS = ["user", "username", "user_name", "account", "subject"]
COMMON_HOST_FIELDS = ["host", "hostname", "computer", "machine", "device"]
COMMON_IP_FIELDS = ["ip", "ip_address", "src_ip", "source_ip", "remote_ip"]
COMMON_EVENT_FIELDS = ["event", "event_type", "action", "type", "category"]


def parse_csv(file_path: str) -> List[Dict[str, Any]]:
    """Parse a CSV log file and normalize to CyberTrace event schema."""
    events = []
    with open(file_path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        headers = [h.lower().strip() for h in (reader.fieldnames or [])]

        ts_field = _find_field(headers, COMMON_TIMESTAMP_FIELDS)
        user_field = _find_field(headers, COMMON_USER_FIELDS)
        host_field = _find_field(headers, COMMON_HOST_FIELDS)
        ip_field = _find_field(headers, COMMON_IP_FIELDS)
        event_field = _find_field(headers, COMMON_EVENT_FIELDS)

        for row in reader:
            normalized = _normalize_row(row, ts_field, user_field, host_field, ip_field, event_field)
            events.append(normalized)

    return events


def _find_field(headers: List[str], candidates: List[str]) -> str:
    for candidate in candidates:
        if candidate in headers:
            return candidate
    return ""


def _normalize_row(row: dict, ts_f, user_f, host_f, ip_f, event_f) -> Dict[str, Any]:
    lower_row = {k.lower().strip(): v for k, v in row.items()}
    return {
        "timestamp": lower_row.get(ts_f, ""),
        "source": "CSV Log",
        "event_type": lower_row.get(event_f, "Log Entry"),
        "user": lower_row.get(user_f, ""),
        "host": lower_row.get(host_f, ""),
        "ip_address": lower_row.get(ip_f, ""),
        "severity": "low",
        "description": " | ".join(f"{k}={v}" for k, v in list(lower_row.items())[:5]),
        "raw_data": dict(lower_row),
    }
