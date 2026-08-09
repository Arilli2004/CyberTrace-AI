"""
Parser Service — Service Orchestrator for Evidence Ingestion & Parsing
"""
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.event_repository import EventRepository
from app.parsers.parser_manager import ParserManager
from app.models import Evidence, Event, SeverityLevel, ProcessingStage


class ParserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.event_repo = EventRepository(db)

    async def parse_evidence_file(self, evidence_id: int, user_id: int) -> Dict[str, Any]:
        """Execute parsing pipeline for an evidence file and persist extracted events."""
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence #{evidence_id} not found.")

        # Update evidence status to parsing
        evidence.parser_status = "parsing"
        await self.db.flush()

        try:
            # Execute async parsing
            parsed_dicts = await ParserManager.parse_file_async(
                file_path=evidence.storage_path,
                extension=evidence.extension,
            )

            # Clear old events if re-parsing
            await self.event_repo.delete_events_for_evidence(evidence.id)

            # Convert dictionaries to Event ORM objects
            event_objects = []
            for d in parsed_dicts:
                event_objects.append(
                    Event(
                        uuid_id=d["uuid_id"],
                        evidence_id=evidence.id,
                        case_id=evidence.case_id,
                        timestamp=d["timestamp"],
                        source=d["source"],
                        event_type=d["event_type"],
                        event_id=d["event_id"],
                        user=d["user"],
                        host=d["host"],
                        ip_address=d["ip_address"],
                        process=d["process"],
                        file_path=d["file_path"],
                        severity=SeverityLevel(d["severity"]),
                        description=d["description"],
                        raw_data=d["raw_data"],
                        is_suspicious=d["is_suspicious"],
                        confidence_score=d["confidence_score"],
                    )
                )

            # Batch insert events into DB
            total_events = await self.event_repo.batch_create_events(event_objects)

            # Update Evidence status & AI pipeline lifecycle stage
            evidence.event_count = total_events
            evidence.is_parsed = True
            evidence.parser_status = "completed"
            evidence.parse_status = "completed"
            evidence.processing_stage = ProcessingStage.PARSED
            await self.db.flush()

            # Record Chain of Custody Audit Log
            await self.evidence_repo.log_custody_action(
                evidence_id=evidence.id,
                user_id=user_id,
                action="PARSE",
                details={
                    "total_events_extracted": total_events,
                    "processing_stage": "PARSED",
                    "extension": evidence.extension,
                },
            )

            return {
                "evidence_id": evidence.id,
                "status": "completed",
                "total_events": total_events,
                "processing_stage": "PARSED",
            }

        except Exception as err:
            evidence.parser_status = "failed"
            evidence.parse_status = "failed"
            await self.db.flush()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Parsing error on evidence #{evidence_id}: {str(err)}",
            )

    async def parse_all_evidence_in_case(self, case_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Parse all evidence files belonging to a case."""
        evidence_list, _ = await self.evidence_repo.list_evidence(case_id=case_id, limit=100)
        results = []

        for e in evidence_list:
            res = await self.parse_evidence_file(evidence_id=e.id, user_id=user_id)
            results.append(res)

        return results

    async def get_parser_status(self, evidence_id: int) -> Dict[str, Any]:
        """Get current parsing status and event count for an evidence file."""
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence #{evidence_id} not found.")

        return {
            "evidence_id": evidence.id,
            "filename": evidence.original_filename,
            "parser_status": evidence.parser_status,
            "processing_stage": evidence.processing_stage,
            "event_count": evidence.event_count,
            "is_parsed": evidence.is_parsed,
        }
