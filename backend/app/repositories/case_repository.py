"""
Case Repository — Encapsulates database queries for Case entities
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List, Tuple
from datetime import datetime

from app.models import Case, CaseStatus


class CaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, case_id: int, investigator_id: Optional[int] = None) -> Optional[Case]:
        """Fetch active (non-deleted) case by integer ID."""
        query = select(Case).where(Case.id == case_id, Case.is_deleted == False)
        if investigator_id is not None:
            query = query.where(Case.investigator_id == investigator_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid_id: str, investigator_id: Optional[int] = None) -> Optional[Case]:
        """Fetch active case by UUID string."""
        query = select(Case).where(Case.uuid_id == uuid_id, Case.is_deleted == False)
        if investigator_id is not None:
            query = query.where(Case.investigator_id == investigator_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_cases(
        self,
        investigator_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[CaseStatus] = None,
        search: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Tuple[List[Case], int]:
        """List cases with pagination, search, status, and priority filters."""
        query = select(Case).where(Case.investigator_id == investigator_id, Case.is_deleted == False)
        
        if status:
            query = query.where(Case.status == status)
        if priority:
            query = query.where(Case.priority == priority)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Case.title.ilike(search_pattern),
                    Case.description.ilike(search_pattern),
                )
            )

        # Count total matches
        count_query = select(func.count()).select_from(query.subquery())
        count_res = await self.db.execute(count_query)
        total = count_res.scalar_one() or 0

        # Execute paginated query
        query = query.order_by(Case.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        cases = result.scalars().all()

        return cases, total

    async def create(self, case: Case) -> Case:
        """Add new case to session."""
        self.db.add(case)
        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def update(self, case: Case, update_data: dict) -> Case:
        """Update case fields."""
        for field, value in update_data.items():
            if hasattr(case, field) and value is not None:
                setattr(case, field, value)
        case.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def soft_delete(self, case: Case) -> None:
        """Perform soft delete by setting is_deleted=True."""
        case.is_deleted = True
        case.deleted_at = datetime.utcnow()
        await self.db.flush()
