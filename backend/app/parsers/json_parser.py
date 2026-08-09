"""
JSON & JSON-Lines Log Parser — CyberTrace AI
"""
import json
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.parsers.base_parser import BaseParser


class JsonParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        events = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()

            if not content:
                return events

            raw_records = []
            # Try parsing as JSON Array or JSON Lines
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    raw_records = data
                elif isinstance(data, dict):
                    raw_records = [data]
            except json.JSONDecodeError:
                # Try JSON Lines format
                for line in content.splitlines():
                    if line.strip():
                        try:
                            raw_records.append(json.loads(line))
                        except Exception:
                            continue

            for rec in raw_records:
                if not isinstance(rec, dict):
                    continue

                rec_lower = {str(k).lower(): v for k, v in rec.items()}

                timestamp = None
                ts_val = rec_lower.get("timestamp") or rec_lower.get("time") or rec_lower.get("@timestamp")
                if isinstance(ts_val, str):
                    try:
                        timestamp = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                    except Exception:
                        pass

                hostname = str(rec_lower.get("hostname") or rec_lower.get("host") or "UNKNOWN_HOST")
                username = str(rec_lower.get("username") or rec_lower.get("user") or "UNKNOWN_USER")
                event_type = str(rec_lower.get("event_type") or rec_lower.get("type") or "JsonLog")
                event_id = str(rec_lower.get("event_id") or rec_lower.get("id") or "")
                severity = str(rec_lower.get("severity") or rec_lower.get("level") or "low")
                ip_address = str(rec_lower.get("ip_address") or rec_lower.get("ip") or rec_lower.get("src_ip") or "")
                process_name = str(rec_lower.get("process") or rec_lower.get("process_name") or "")
                file_path_field = str(rec_lower.get("file_path") or rec_lower.get("path") or "")
                description = str(rec_lower.get("description") or rec_lower.get("message") or json.dumps(rec))

                events.append(
                    self.create_event_dict(
                        timestamp=timestamp,
                        hostname=hostname,
                        username=username,
                        event_type=event_type,
                        event_id=event_id,
                        severity=severity,
                        source="JsonLog",
                        ip_address=ip_address,
                        process_name=process_name,
                        file_path=file_path_field,
                        description=description[:500],
                        raw_event=rec,
                    )
                )

        except Exception as e:
            print(f"JsonParser Error on {file_path}: {e}")

        return events
