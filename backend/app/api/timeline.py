"""
Timeline API — Retrieve correlated event timelines for a case
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.database.connection import get_db
from app.models import Event, Evidence, Case, SeverityLevel
from app.core.security import get_current_user_id

router = APIRouter()


@router.get("/{case_id}")
async def get_timeline(
    case_id: int,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    severity: Optional[SeverityLevel] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get chronological event timeline for a case."""
    # Verify case ownership
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.investigator_id == user_id)
    )
    if not case_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    # Build query
    query = (
        select(Event)
        .join(Evidence, Event.evidence_id == Evidence.id)
        .where(Evidence.case_id == case_id)
    )
    if start:
        query = query.where(Event.timestamp >= start)
    if end:
        query = query.where(Event.timestamp <= end)
    if severity:
        query = query.where(Event.severity == severity)

    query = query.order_by(Event.timestamp).offset(skip).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "case_id": case_id,
        "total": len(events),
        "events": events,
    }


@router.get("/{case_id}/suspicious")
async def get_suspicious_events(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get only suspicious/flagged events for a case."""
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.investigator_id == user_id)
    )
    if not case_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    query = (
        select(Event)
        .join(Evidence, Event.evidence_id == Evidence.id)
        .where(Evidence.case_id == case_id, Event.is_suspicious == True)
        .order_by(Event.confidence_score.desc(), Event.timestamp)
    )
    result = await db.execute(query)
    return result.scalars().all()
