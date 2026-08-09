"""
Event Repository — Batch Insertion & Query Access Layer
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from typing import Optional, List, Tuple

from app.models import Event, SeverityLevel


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def batch_create_events(self, events: List[Event], batch_size: int = 1000) -> int:
        """Batch insert Event ORM objects into the database."""
        total = len(events)
        for i in range(0, total, batch_size):
            chunk = events[i : i + batch_size]
            self.db.add_all(chunk)
            await self.db.flush()
        return total

    async def get_by_id(self, event_id: int) -> Optional[Event]:
        """Get event by primary key ID."""
        result = await self.db.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def list_events_by_case(
        self,
        case_id: int,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        severity: Optional[SeverityLevel] = None,
    ) -> Tuple[List[Event], int]:
        """Fetch paginated events for a case."""
        query = select(Event).where(Event.case_id == case_id)

        if severity:
            query = query.where(Event.severity == severity)
        if search:
            search_pat = f"%{search}%"
            query = query.where(
                or_(
                    Event.description.ilike(search_pat),
                    Event.user.ilike(search_pat),
                    Event.host.ilike(search_pat),
                    Event.process.ilike(search_pat),
                    Event.ip_address.ilike(search_pat),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one() or 0

        # Execute paginated search
        query = query.order_by(Event.timestamp.asc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        events = result.scalars().all()

        return events, total

    async def delete_events_for_evidence(self, evidence_id: int) -> None:
        """Clear old parsed events before re-parsing."""
        await self.db.execute(delete(Event).where(Event.evidence_id == evidence_id))
        await self.db.flush()
