"""
Normalized Event Repository — Batch Persistence & Query Access Layer
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from typing import Optional, List, Tuple

from app.models import NormalizedEvent, EventCategory, SeverityLevel


class NormalizedEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def batch_create_normalized_events(self, events: List[NormalizedEvent], batch_size: int = 1000) -> int:
        """Batch insert NormalizedEvent objects into database."""
        total = len(events)
        for i in range(0, total, batch_size):
            chunk = events[i : i + batch_size]
            self.db.add_all(chunk)
            await self.db.flush()
        return total

    async def get_by_id(self, event_id: int) -> Optional[NormalizedEvent]:
        result = await self.db.execute(select(NormalizedEvent).where(NormalizedEvent.id == event_id))
        return result.scalar_one_or_none()

    async def list_normalized_events_by_case(
        self,
        case_id: int,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        category: Optional[EventCategory] = None,
        severity: Optional[SeverityLevel] = None,
    ) -> Tuple[List[NormalizedEvent], int]:
        """Fetch paginated normalized events for a case."""
        query = select(NormalizedEvent).where(NormalizedEvent.case_id == case_id)

        if category:
            query = query.where(NormalizedEvent.event_category == category)
        if severity:
            query = query.where(NormalizedEvent.severity == severity)
        if search:
            search_pat = f"%{search}%"
            query = query.where(
                or_(
                    NormalizedEvent.action.ilike(search_pat),
                    NormalizedEvent.username.ilike(search_pat),
                    NormalizedEvent.hostname.ilike(search_pat),
                    NormalizedEvent.ip_address.ilike(search_pat),
                    NormalizedEvent.process_name.ilike(search_pat),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one() or 0

        query = query.order_by(NormalizedEvent.timestamp_utc.asc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        events = result.scalars().all()

        return events, total

    async def delete_for_evidence(self, evidence_id: int) -> None:
        """Clear previous normalized events before re-normalizing."""
        await self.db.execute(delete(NormalizedEvent).where(NormalizedEvent.evidence_id == evidence_id))
        await self.db.flush()
