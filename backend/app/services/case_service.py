"""
Case Service — Business Logic for Investigation Cases
"""
from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.repositories.case_repository import CaseRepository
from app.schemas.cases import CaseCreateSchema, CaseUpdateSchema
from app.models import Case, CaseStatus


class CaseService:
    def __init__(self, db: AsyncSession):
        self.repository = CaseRepository(db)

    async def list_cases_for_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[CaseStatus] = None,
        search: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Tuple[List[Case], int]:
        """Fetch cases belonging to investigator with filtering and search."""
        return await self.repository.list_cases(
            investigator_id=user_id,
            skip=skip,
            limit=limit,
            status=status,
            search=search,
            priority=priority,
        )

    async def create_case(self, user_id: int, data: CaseCreateSchema) -> Case:
        """Create and persist a new investigation case."""
        new_case = Case(
            uuid_id=str(uuid.uuid4()),
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            priority=data.priority,
            investigator_id=user_id,
            status=CaseStatus.new,
            is_deleted=False,
        )
        return await self.repository.create(new_case)

    async def get_case_by_id(self, case_id: int, user_id: int) -> Case:
        """Retrieve case by ID ensuring user authorization."""
        case = await self.repository.get_by_id(case_id, investigator_id=user_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found or access denied.",
            )
        return case

    async def update_case(self, case_id: int, user_id: int, data: CaseUpdateSchema) -> Case:
        """Update case details."""
        case = await self.get_case_by_id(case_id, user_id)
        update_dict = data.model_dump(exclude_none=True)
        return await self.repository.update(case, update_dict)

    async def delete_case(self, case_id: int, user_id: int) -> None:
        """Soft-delete an investigation case."""
        case = await self.get_case_by_id(case_id, user_id)
        await self.repository.soft_delete(case)
