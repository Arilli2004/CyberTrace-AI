"""
CSV Log Parser — Automated Field Mapping & Universal Normalization
"""
import csv
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.parsers.base_parser import BaseParser


class CsvParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        events = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row:
                        continue

                    # Dynamic Field Discovery (Case-insensitive matching)
                    row_lower = {str(k).lower(): str(v).strip() for k, v in row.items() if k}

                    timestamp = None
                    ts_val = (
                        row_lower.get("timestamp")
                        or row_lower.get("time")
                        or row_lower.get("date")
                        or row_lower.get("created_at")
                    )
                    if ts_val:
                        try:
                            timestamp = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                        except Exception:
                            pass

                    hostname = row_lower.get("hostname") or row_lower.get("host") or row_lower.get("computer")
                    username = row_lower.get("username") or row_lower.get("user") or row_lower.get("account")
                    event_type = row_lower.get("event_type") or row_lower.get("action") or "CSVRecord"
                    event_id = row_lower.get("event_id") or row_lower.get("id")
                    severity = row_lower.get("severity") or row_lower.get("level") or "low"
                    ip_address = row_lower.get("ip_address") or row_lower.get("ip") or row_lower.get("src_ip")
                    process_name = row_lower.get("process") or row_lower.get("process_name")
                    file_path_field = row_lower.get("file_path") or row_lower.get("path")
                    description = row_lower.get("description") or row_lower.get("message") or str(row)

                    events.append(
                        self.create_event_dict(
                            timestamp=timestamp,
                            hostname=hostname,
                            username=username,
                            event_type=event_type,
                            event_id=event_id,
                            severity=severity,
                            source="CSVFile",
                            ip_address=ip_address,
                            process_name=process_name,
                            file_path=file_path_field,
                            description=description[:500],
                            raw_event=dict(row),
                        )
                    )

        except Exception as e:
            print(f"CsvParser Error on {file_path}: {e}")

        return events
