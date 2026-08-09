"""
Parser & Events API Router — Multi-Format Evidence Parsing Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database.connection import get_db
from app.services.parser_service import ParserService
from app.repositories.event_repository import EventRepository
from app.schemas.parser import (
    ParserStatusSchema,
    EventResponseSchema,
    EventListResponseSchema,
)
from app.models import SeverityLevel
from app.core.security import get_current_user_id

router = APIRouter()


def get_parser_service(db: AsyncSession = Depends(get_db)) -> ParserService:
    return ParserService(db)


def get_event_repo(db: AsyncSession = Depends(get_db)) -> EventRepository:
    return EventRepository(db)


@router.post(
    "/parse/{evidence_id}",
    response_model=ParserStatusSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Evidence Parsing",
    description="Parse an evidence log file into structured digital events.",
)
async def parse_evidence(
    evidence_id: int,
    service: ParserService = Depends(get_parser_service),
    user_id: int = Depends(get_current_user_id),
):
    res = await service.parse_evidence_file(evidence_id=evidence_id, user_id=user_id)
    return {
        "evidence_id": res["evidence_id"],
        "filename": "",
        "parser_status": res["status"],
        "processing_stage": res["processing_stage"],
        "event_count": res["total_events"],
        "is_parsed": True,
    }


@router.post(
    "/parse-all/{case_id}",
    response_model=List[ParserStatusSchema],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Parse All Evidence in Case",
    description="Parse all unparsed evidence log files belonging to a specific case.",
)
async def parse_all_evidence(
    case_id: int,
    service: ParserService = Depends(get_parser_service),
    user_id: int = Depends(get_current_user_id),
):
    results = await service.parse_all_evidence_in_case(case_id=case_id, user_id=user_id)
    return [
        {
            "evidence_id": r["evidence_id"],
            "filename": "",
            "parser_status": r["status"],
            "processing_stage": r["processing_stage"],
            "event_count": r["total_events"],
            "is_parsed": True,
        }
        for r in results
    ]


@router.get(
    "/status/{evidence_id}",
    response_model=ParserStatusSchema,
    summary="Get Parser Status",
    description="Query current parsing status and total extracted events for an evidence file.",
)
async def get_parser_status(
    evidence_id: int,
    service: ParserService = Depends(get_parser_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_parser_status(evidence_id=evidence_id)


# ─── Events Endpoints ─────────────────────────────────────────────────────────
@router.get(
    "/events/case/{case_id}",
    response_model=EventListResponseSchema,
    summary="Get Case Parsed Events",
    description="Fetch paginated list of extracted events for an investigation case.",
)
async def list_case_events(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search description, user, host, or IP"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity"),
    repo: EventRepository = Depends(get_event_repo),
    user_id: int = Depends(get_current_user_id),
):
    events, total = await repo.list_events_by_case(
        case_id=case_id, skip=skip, limit=limit, search=search, severity=severity
    )
    return {"events": events, "total": total, "skip": skip, "limit": limit}


@router.get(
    "/events/{event_id}",
    response_model=EventResponseSchema,
    summary="Get Event Details",
    description="Retrieve detailed parsed event payload by ID.",
)
async def get_event_details(
    event_id: int,
    repo: EventRepository = Depends(get_event_repo),
    user_id: int = Depends(get_current_user_id),
):
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event #{event_id} not found.")
    return event
