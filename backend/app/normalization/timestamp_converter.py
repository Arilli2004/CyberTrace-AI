"""
Timestamp Converter — Timezone Handler & UTC Normalizer
"""
from datetime import datetime, timezone
from typing import Union, Optional


class TimestampConverter:
    @classmethod
    def to_utc(cls, dt: Optional[Union[datetime, str, int, float]]) -> datetime:
        """
        Convert any datetime, string, or timestamp representation into a timezone-aware UTC datetime.
        """
        if dt is None:
            return datetime.now(timezone.utc)

        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        if isinstance(dt, (int, float)):
            try:
                return datetime.fromtimestamp(dt, tz=timezone.utc)
            except Exception:
                return datetime.now(timezone.utc)

        if isinstance(dt, str):
            try:
                clean_str = dt.replace("Z", "+00:00")
                parsed = datetime.fromisoformat(clean_str)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except Exception:
                pass

        return datetime.now(timezone.utc)
