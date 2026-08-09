"""
Plain Text Log Parser — CyberTrace AI
"""
from typing import List, Dict, Any
from app.parsers.base_parser import BaseParser


class TxtParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        events = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        events.append(
                            self.create_event_dict(
                                source="TextLog",
                                event_type="LogLine",
                                description=line_str[:500],
                                raw_event={"line": line_str},
                            )
                        )

        except Exception as e:
            print(f"TxtParser Error on {file_path}: {e}")

        return events
