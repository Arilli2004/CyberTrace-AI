"""
Evidence Repository — Encapsulates Database Access for Evidence and Chain of Custody
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List, Tuple
from datetime import datetime

from app.models import Evidence, ChainOfCustodyLog, EvidenceType


class EvidenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, evidence_id: int) -> Optional[Evidence]:
        """Fetch active evidence record by ID."""
        query = select(Evidence).where(Evidence.id == evidence_id, Evidence.is_deleted == False)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid_id: str) -> Optional[Evidence]:
        """Fetch active evidence record by UUID."""
        query = select(Evidence).where(Evidence.uuid_id == uuid_id, Evidence.is_deleted == False)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_sha256_in_case(self, case_id: int, sha256_hash: str) -> Optional[Evidence]:
        """Check for existing duplicate SHA256 hash in a case."""
        query = select(Evidence).where(
            Evidence.case_id == case_id,
            Evidence.sha256 == sha256_hash,
            Evidence.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_evidence(
        self,
        case_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        file_type: Optional[EvidenceType] = None,
    ) -> Tuple[List[Evidence], int]:
        """List evidence with optional case filtering, search, and pagination."""
        query = select(Evidence).where(Evidence.is_deleted == False)

        if case_id is not None:
            query = query.where(Evidence.case_id == case_id)
        if file_type:
            query = query.where(Evidence.file_type == file_type)
        if search:
            search_pat = f"%{search}%"
            query = query.where(
                or_(
                    Evidence.filename.ilike(search_pat),
                    Evidence.original_filename.ilike(search_pat),
                    Evidence.sha256.ilike(search_pat),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one() or 0

        # Execute page query
        query = query.order_by(Evidence.uploaded_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        evidence_list = result.scalars().all()

        return evidence_list, total

    async def create(self, evidence: Evidence) -> Evidence:
        """Create new evidence record."""
        self.db.add(evidence)
        await self.db.flush()
        await self.db.refresh(evidence)
        return evidence

    async def update(self, evidence: Evidence, update_data: dict) -> Evidence:
        """Update fields on evidence."""
        for field, value in update_data.items():
            if hasattr(evidence, field) and value is not None:
                setattr(evidence, field, value)
        evidence.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(evidence)
        return evidence

    async def soft_delete(self, evidence: Evidence) -> None:
        """Soft delete evidence."""
        evidence.is_deleted = True
        evidence.deleted_at = datetime.utcnow()
        await self.db.flush()

    async def log_custody_action(self, evidence_id: int, user_id: Optional[int], action: str, details: Optional[dict] = None) -> ChainOfCustodyLog:
        """Record a Chain of Custody audit log entry."""
        log_entry = ChainOfCustodyLog(
            evidence_id=evidence_id,
            user_id=user_id,
            action=action,
            details=details or {},
        )
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry

    async def get_custody_logs(self, evidence_id: int) -> List[ChainOfCustodyLog]:
        """Fetch all Chain of Custody audit log entries for an evidence file."""
        query = select(ChainOfCustodyLog).where(ChainOfCustodyLog.evidence_id == evidence_id).order_by(ChainOfCustodyLog.timestamp.asc())
        result = await self.db.execute(query)
        return result.scalars().all()
