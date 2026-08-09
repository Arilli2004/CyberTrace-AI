"""
Linux Syslog & Auth.log Parser — CyberTrace AI
"""
import re
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.parsers.base_parser import BaseParser


class LinuxParser(BaseParser):

    # Standard Syslog Regex: Month Day HH:MM:SS Hostname Process[PID]: Message
    SYSLOG_REGEX = re.compile(
        r"^(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
        r"(?P<host>[\w\.\-]+)\s+(?P<process>[\w\.\-\(\)]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)$"
    )

    MONTHS = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        events = []
        current_year = datetime.now(timezone.utc).year

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue

                    match = self.SYSLOG_REGEX.match(line_str)
                    if match:
                        data = match.groupdict()
                        month = self.MONTHS.get(data["month"], 1)
                        day = int(data["day"])
                        time_parts = [int(p) for p in data["time"].split(":")]

                        timestamp = datetime(
                            current_year, month, day, time_parts[0], time_parts[1], time_parts[2], tzinfo=timezone.utc
                        )

                        message = data["message"]
                        process = data["process"]
                        host = data["host"]

                        # Determine severity & event details based on auth.log patterns
                        severity = "low"
                        user = None
                        ip = None
                        event_type = "SyslogMessage"

                        if "Failed password" in message or "authentication failure" in message:
                            severity = "critical"
                            event_type = "AuthFailure"
                            user_match = re.search(r"for (invalid user )?(\w+)", message)
                            if user_match:
                                user = user_match.group(2)
                            ip_match = re.search(r"from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", message)
                            if ip_match:
                                ip = ip_match.group(1)

                        elif "Accepted password" in message or "session opened" in message:
                            severity = "high"
                            event_type = "AuthSuccess"
                            user_match = re.search(r"for (\w+)", message)
                            if user_match:
                                user = user_match.group(1)
                            ip_match = re.search(r"from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", message)
                            if ip_match:
                                ip = ip_match.group(1)

                        elif "sudo:" in message or "root" in message:
                            severity = "medium"
                            event_type = "PrivilegeEscalation"

                        events.append(
                            self.create_event_dict(
                                timestamp=timestamp,
                                hostname=host,
                                username=user or "root",
                                event_type=event_type,
                                event_id=process,
                                severity=severity,
                                source="LinuxSyslog",
                                ip_address=ip,
                                process_name=process,
                                description=message[:500],
                                raw_event={"raw_line": line_str},
                            )
                        )
                    else:
                        # Fallback for non-standard log lines
                        events.append(
                            self.create_event_dict(
                                source="LinuxLog",
                                event_type="LogLine",
                                description=line_str[:500],
                                raw_event={"raw_line": line_str},
                            )
                        )

        except Exception as e:
            print(f"LinuxParser Error on {file_path}: {e}")

        return events
