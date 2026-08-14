"""
Cases API Router — Controller Layer for Investigation Cases & Live Dashboard Stats
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database.connection import get_db
from app.services.case_service import CaseService
from app.schemas.cases import (
    CaseCreateSchema,
    CaseUpdateSchema,
    CaseResponseSchema,
    CaseListResponseSchema,
)
from app.models import Case, CaseStatus, Evidence, Event, SeverityLevel, ChainOfCustodyLog
from app.core.security import get_current_user_id

router = APIRouter()


# ─── Service Dependency ───────────────────────────────────────────────────────
def get_case_service(db: AsyncSession = Depends(get_db)) -> CaseService:
    return CaseService(db)


# ─── Endpoints ───────────────────────────────────────────────────────────────
@router.get(
    "/stats/dashboard",
    summary="Get Live Dashboard Statistics",
    description="Retrieve live database metrics for total cases, evidence files, active alerts, built timelines, and recent activities.",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    # 1. Total Cases
    cases_stmt = select(func.count(Case.id)).where(Case.is_deleted == False)
    cases_res = await db.execute(cases_stmt)
    total_cases = cases_res.scalar() or 0

    # 2. Total Evidence Files
    ev_stmt = select(func.count(Evidence.id)).where(Evidence.is_deleted == False)
    ev_res = await db.execute(ev_stmt)
    total_evidence = ev_res.scalar() or 0

    # 3. Active Threat Alerts (High / Critical events)
    alert_stmt = select(func.count(Event.id)).where(
        Event.severity.in_([SeverityLevel.high, SeverityLevel.critical])
    )
    alert_res = await db.execute(alert_stmt)
    active_alerts = alert_res.scalar() or 0

    # 4. Timelines Built (Parsed Evidence count)
    parsed_stmt = select(func.count(Evidence.id)).where(
        Evidence.is_deleted == False, Evidence.is_parsed == True
    )
    parsed_res = await db.execute(parsed_stmt)
    timelines_built = parsed_res.scalar() or 0

    # 5. Recent Custody Logs / Activity Feed from DB
    logs_stmt = (
        select(ChainOfCustodyLog)
        .order_by(ChainOfCustodyLog.timestamp.desc())
        .limit(6)
    )
    logs_res = await db.execute(logs_stmt)
    recent_logs = logs_res.scalars().all()

    activity_feed = [
        {
            "id": log.id,
            "action": f"Action '{log.action}' performed on Evidence #{log.evidence_id}",
            "time": log.timestamp.strftime("%Y-%m-%d %H:%M UTC") if log.timestamp else "Recently",
            "details": log.details or {},
            "severity": "critical" if log.action in ["DELETE", "PARSE_FAIL"] else "high" if log.action == "PARSE" else "info",
        }
        for log in recent_logs
    ]

    return {
        "total_cases": total_cases,
        "total_evidence": total_evidence,
        "active_alerts": active_alerts,
        "timelines_built": timelines_built,
        "activity_feed": activity_feed,
    }


@router.get(
    "/",
    response_model=CaseListResponseSchema,
    summary="List Investigation Cases",
    description="Fetch paginated list of cases for current investigator with search and filter support.",
)
async def list_cases(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum cases per page"),
    status: Optional[CaseStatus] = Query(None, description="Filter by case status"),
    search: Optional[str] = Query(None, description="Search case title or description"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, medium, high, critical)"),
    service: CaseService = Depends(get_case_service),
    user_id: int = Depends(get_current_user_id),
):
    cases, total = await service.list_cases_for_user(
        user_id=user_id,
        skip=skip,
        limit=limit,
        status=status,
        search=search,
        priority=priority,
    )
    return {
        "cases": cases,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post(
    "/",
    response_model=CaseResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Case",
    description="Initialize a new digital evidence investigation case.",
)
async def create_case(
    body: CaseCreateSchema,
    service: CaseService = Depends(get_case_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.create_case(user_id=user_id, data=body)


@router.get(
    "/{case_id}",
    response_model=CaseResponseSchema,
    summary="Get Case Details",
    description="Retrieve a specific investigation case by ID.",
)
async def get_case(
    case_id: int,
    service: CaseService = Depends(get_case_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_case_by_id(case_id=case_id, user_id=user_id)


@router.put(
    "/{case_id}",
    response_model=CaseResponseSchema,
    summary="Update Case",
    description="Update title, description, priority, or status of an existing case.",
)
async def update_case(
    case_id: int,
    body: CaseUpdateSchema,
    service: CaseService = Depends(get_case_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.update_case(case_id=case_id, user_id=user_id, data=body)


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft Delete Case",
    description="Safely soft-delete an investigation case.",
)
async def delete_case(
    case_id: int,
    service: CaseService = Depends(get_case_service),
    user_id: int = Depends(get_current_user_id),
):
    await service.delete_case(case_id=case_id, user_id=user_id)
