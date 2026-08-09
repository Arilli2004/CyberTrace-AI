"""
Linux Log Parser — Parse syslog, auth.log, secure, kern.log
"""
import re
from typing import List, Dict, Any
from datetime import datetime


# Common syslog format: Mon DD HH:MM:SS host process[pid]: message
SYSLOG_PATTERN = re.compile(
    r"(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<process>[^\[:\s]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<message>.+)"
)

# Auth.log keywords
SUSPICIOUS_KEYWORDS = [
    "failed", "invalid", "error", "denied", "unauthorized", "sudo", "su:",
    "authentication failure", "bad password", "root login", "accepted password",
    "session opened", "session closed", "useradd", "userdel", "passwd"
]


def parse_linux_log(file_path: str) -> List[Dict[str, Any]]:
    """Parse a Linux log file (syslog, auth.log, etc.)."""
    events = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = _parse_line(line)
            events.append(event)
    return events


def _parse_line(line: str) -> Dict[str, Any]:
    match = SYSLOG_PATTERN.match(line)
    if match:
        g = match.groupdict()
        message = g.get("message", "")
        severity = _detect_severity(message)
        is_suspicious = any(kw in message.lower() for kw in SUSPICIOUS_KEYWORDS)

        return {
            "timestamp": f"{g['month']} {g['day']} {g['time']}",
            "source": "Linux Syslog",
            "event_type": _classify_event(g.get("process", ""), message),
            "host": g.get("host", ""),
            "user": _extract_user(message),
            "process": g.get("process", ""),
            "severity": severity,
            "description": message[:200],
            "is_suspicious": is_suspicious,
            "raw_data": {"line": line, "pid": g.get("pid", "")},
        }

    return {
        "timestamp": "",
        "source": "Linux Log",
        "event_type": "Log Entry",
        "description": line[:200],
        "severity": "low",
        "raw_data": {"line": line},
    }


def _detect_severity(message: str) -> str:
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in ["critical", "emergency", "alert", "panic"]):
        return "critical"
    if any(kw in msg_lower for kw in ["error", "failed", "denied", "invalid"]):
        return "high"
    if any(kw in msg_lower for kw in ["warning", "warn", "sudo"]):
        return "medium"
    return "low"


def _classify_event(process: str, message: str) -> str:
    p = process.lower()
    m = message.lower()
    if "sshd" in p:
        if "accepted" in m:
            return "SSH Login Success"
        if "failed" in m or "invalid" in m:
            return "SSH Login Failure"
        return "SSH Event"
    if "sudo" in p:
        return "Sudo Command"
    if "su" == p:
        return "Switch User"
    if "useradd" in p or "adduser" in p:
        return "User Created"
    if "userdel" in p:
        return "User Deleted"
    if "passwd" in p:
        return "Password Changed"
    if "cron" in p:
        return "Cron Job"
    return "System Event"


def _extract_user(message: str) -> str:
    patterns = [
        r"user (\w+)",
        r"for (?:user )?(\w+)(?:\s|$)",
        r"from user (\w+)",
        r"by (\w+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""
