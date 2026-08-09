"""
Normalization API Router — Universal Evidence Normalization Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database.connection import get_db
from app.services.normalization_service import NormalizationService
from app.repositories.normalized_event_repository import NormalizedEventRepository
from app.schemas.normalization import (
    NormalizationStatusSchema,
    NormalizedEventResponseSchema,
    NormalizedEventListResponseSchema,
)
from app.models import EventCategory, SeverityLevel
from app.core.security import get_current_user_id

router = APIRouter()


def get_normalization_service(db: AsyncSession = Depends(get_db)) -> NormalizationService:
    return NormalizationService(db)


def get_norm_repo(db: AsyncSession = Depends(get_db)) -> NormalizedEventRepository:
    return NormalizedEventRepository(db)


@router.post(
    "/normalize/{evidence_id}",
    response_model=NormalizationStatusSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Evidence Normalization",
    description="Normalize raw parsed events into universal forensic event schema.",
)
async def normalize_evidence(
    evidence_id: int,
    service: NormalizationService = Depends(get_normalization_service),
    user_id: int = Depends(get_current_user_id),
):
    res = await service.normalize_evidence(evidence_id=evidence_id, user_id=user_id)
    return {
        "evidence_id": res["evidence_id"],
        "filename": "",
        "normalization_status": res["status"],
        "processing_stage": res["processing_stage"],
        "event_count": res["total_normalized"],
    }


@router.post(
    "/normalize/case/{case_id}",
    response_model=List[NormalizationStatusSchema],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Bulk Normalize Case Evidence",
    description="Normalize all parsed evidence log files in a case.",
)
async def normalize_case(
    case_id: int,
    service: NormalizationService = Depends(get_normalization_service),
    user_id: int = Depends(get_current_user_id),
):
    results = await service.normalize_case(case_id=case_id, user_id=user_id)
    return [
        {
            "evidence_id": r["evidence_id"],
            "filename": "",
            "normalization_status": r["status"],
            "processing_stage": r["processing_stage"],
            "event_count": r["total_normalized"],
        }
        for r in results
    ]


@router.get(
    "/normalize/status/{evidence_id}",
    response_model=NormalizationStatusSchema,
    summary="Get Normalization Status",
    description="Query current normalization status and event count for an evidence file.",
)
async def get_normalization_status(
    evidence_id: int,
    service: NormalizationService = Depends(get_normalization_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_normalization_status(evidence_id=evidence_id)


# ─── Normalized Events Endpoints ──────────────────────────────────────────────
@router.get(
    "/normalized-events/{case_id}",
    response_model=NormalizedEventListResponseSchema,
    summary="Get Case Normalized Events",
    description="Fetch paginated list of normalized forensic events for a case.",
)
async def list_normalized_events(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search action, username, host, or IP"),
    category: Optional[EventCategory] = Query(None, description="Filter by event category"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity"),
    repo: NormalizedEventRepository = Depends(get_norm_repo),
    user_id: int = Depends(get_current_user_id),
):
    events, total = await repo.list_normalized_events_by_case(
        case_id=case_id, skip=skip, limit=limit, search=search, category=category, severity=severity
    )
    return {"events": events, "total": total, "skip": skip, "limit": limit}


@router.get(
    "/normalized-events/detail/{event_id}",
    response_model=NormalizedEventResponseSchema,
    summary="Get Normalized Event Details",
    description="Retrieve detailed normalized event schema by ID.",
)
async def get_normalized_event_details(
    event_id: int,
    repo: NormalizedEventRepository = Depends(get_norm_repo),
    user_id: int = Depends(get_current_user_id),
):
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Normalized event #{event_id} not found.")
    return event
