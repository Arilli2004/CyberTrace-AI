"""
Normalization Service — Normalization Engine Orchestrator
"""
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.event_repository import EventRepository
from app.repositories.normalized_event_repository import NormalizedEventRepository
from app.normalization.normalization_manager import NormalizationManager
from app.models import Evidence, ProcessingStage


class NormalizationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.event_repo = EventRepository(db)
        self.norm_event_repo = NormalizedEventRepository(db)

    async def normalize_evidence(self, evidence_id: int, user_id: int) -> Dict[str, Any]:
        """Execute normalization engine for an evidence file's parsed events."""
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence #{evidence_id} not found.")

        # Fetch parsed events from events table
        parsed_events, total_raw = await self.event_repo.list_events_by_case(
            case_id=evidence.case_id, limit=10000
        )
        evidence_events = [e for e in parsed_events if e.evidence_id == evidence.id]

        if not evidence_events:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Evidence #{evidence_id} has 0 parsed events. Please parse the evidence first.",
            )

        # Clear old normalized records if re-normalizing
        await self.norm_event_repo.delete_for_evidence(evidence.id)

        # Normalize in CPU thread pool
        normalized_objects = []
        for raw_evt in evidence_events:
            norm_obj = await asyncio.to_thread(NormalizationManager.normalize_event, raw_evt)
            normalized_objects.append(norm_obj)

        # Batch insert into normalized_events
        total_normalized = await self.norm_event_repo.batch_create_normalized_events(normalized_objects)

        # Update Evidence processing stage
        evidence.normalization_status = "completed"
        evidence.processing_stage = ProcessingStage.NORMALIZED
        await self.db.flush()

        # Log Chain of Custody Audit Log
        await self.evidence_repo.log_custody_action(
            evidence_id=evidence.id,
            user_id=user_id,
            action="NORMALIZE",
            details={
                "total_events_normalized": total_normalized,
                "processing_stage": "NORMALIZED",
            },
        )

        return {
            "evidence_id": evidence.id,
            "status": "completed",
            "total_normalized": total_normalized,
            "processing_stage": "NORMALIZED",
        }

    async def normalize_case(self, case_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Bulk normalize all parsed evidence files in a case."""
        evidence_list, _ = await self.evidence_repo.list_evidence(case_id=case_id, limit=100)
        results = []

        for e in evidence_list:
            if e.is_parsed:
                res = await self.normalize_evidence(evidence_id=e.id, user_id=user_id)
                results.append(res)

        return results

    async def get_normalization_status(self, evidence_id: int) -> Dict[str, Any]:
        """Query normalization status for an evidence file."""
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence #{evidence_id} not found.")

        return {
            "evidence_id": evidence.id,
            "filename": evidence.original_filename,
            "normalization_status": evidence.normalization_status,
            "processing_stage": evidence.processing_stage,
            "event_count": evidence.event_count,
        }
