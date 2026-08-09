"""
Reports API — Generate and export investigation reports
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.responses import FileResponse
import os

from app.database.connection import get_db
from app.models import Case, AIReport
from app.core.security import get_current_user_id

router = APIRouter()


@router.get("/case/{case_id}")
async def get_reports(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get all AI reports for a case."""
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.investigator_id == user_id)
    )
    if not case_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    result = await db.execute(
        select(AIReport).where(AIReport.case_id == case_id).order_by(AIReport.generated_at.desc())
    )
    return result.scalars().all()


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Download a generated report file."""
    result = await db.execute(
        select(AIReport).join(Case).where(
            AIReport.id == report_id, Case.investigator_id == user_id
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.report_path or not os.path.exists(report.report_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(report.report_path, media_type="application/pdf", filename=f"report_{report_id}.pdf")
