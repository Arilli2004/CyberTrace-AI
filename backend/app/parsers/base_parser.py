"""
Base Abstract Parser Interface — Universal Event Normalization Standard
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid


class BaseParser(ABC):
    """Abstract Base Class for all digital forensic log parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a forensic log file into a list of universal normalized event dictionaries.
        Must be implemented by each specialized parser.
        """
        pass

    @staticmethod
    def create_event_dict(
        timestamp: Optional[datetime] = None,
        hostname: Optional[str] = None,
        username: Optional[str] = None,
        event_type: Optional[str] = "GenericLog",
        event_id: Optional[str] = None,
        severity: Optional[str] = "low",
        source: Optional[str] = "UnknownSource",
        ip_address: Optional[str] = None,
        process_name: Optional[str] = None,
        file_path: Optional[str] = None,
        description: Optional[str] = None,
        raw_event: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Construct a normalized event dictionary complying with the universal schema.
        Used across all future AI reasoning modules (CSP, UCS, A*, Forward/Backward Chaining).
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        elif timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        sev = (severity or "low").lower()
        if sev not in ("low", "medium", "high", "critical"):
            sev = "low"

        return {
            "uuid_id": str(uuid.uuid4()),
            "timestamp": timestamp,
            "host": (hostname or "UNKNOWN_HOST")[:100],
            "user": (username or "UNKNOWN_USER")[:100],
            "event_type": (event_type or "LogEntry")[:100],
            "event_id": str(event_id)[:50] if event_id else None,
            "severity": sev,
            "source": (source or "System")[:100],
            "ip_address": (ip_address or None)[:45] if ip_address else None,
            "process": (process_name or None)[:255] if process_name else None,
            "file_path": (file_path or None)[:500] if file_path else None,
            "description": description or f"Parsed event from {source}",
            "raw_data": raw_event or {},
            "is_suspicious": sev in ("high", "critical"),
            "confidence_score": 0.9 if sev == "critical" else (0.7 if sev == "high" else 0.2),
        }
