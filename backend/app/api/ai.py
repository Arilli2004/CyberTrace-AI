"""
AI API — LLM-powered investigation assistant and report generation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.models import Case, Event, Evidence, AIReport
from app.core.security import get_current_user_id
from app.core.config import settings

router = APIRouter()


class AnalyzeRequest(BaseModel):
    case_id: int
    question: Optional[str] = None


class ReportRequest(BaseModel):
    case_id: int
    report_type: str = "full"  # full | summary | executive


async def _build_context(case_id: int, db: AsyncSession) -> str:
    """Build investigation context from case events."""
    query = (
        select(Event)
        .join(Evidence, Event.evidence_id == Evidence.id)
        .where(Evidence.case_id == case_id)
        .order_by(Event.timestamp)
        .limit(200)
    )
    result = await db.execute(query)
    events = result.scalars().all()

    lines = []
    for e in events:
        lines.append(
            f"[{e.timestamp}] [{e.severity}] {e.event_type} | User: {e.user} | Host: {e.host} | {e.description}"
        )
    return "\n".join(lines)


@router.post("/analyze")
async def analyze_case(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """AI-powered analysis of a case with optional investigator question."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    # Verify case
    case_result = await db.execute(
        select(Case).where(Case.id == body.case_id, Case.investigator_id == user_id)
    )
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    context = await _build_context(body.case_id, db)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        system_prompt = """You are CyberTrace AI, an expert digital forensics investigator.
Analyze the provided digital evidence timeline and:
1. Identify suspicious activities and attack patterns
2. Determine the likely root cause
3. Assess the risk level (Low/Medium/High/Critical)
4. Provide a brief executive summary
5. List recommended next investigation steps

Be concise, factual, and evidence-based."""

        user_message = f"Case: {case.title}\n\nEvidence Timeline:\n{context}"
        if body.question:
            user_message += f"\n\nInvestigator Question: {body.question}"

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

        analysis = response.choices[0].message.content
        return {"case_id": body.case_id, "analysis": analysis, "model": settings.OPENAI_MODEL}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@router.post("/report")
async def generate_report(
    body: ReportRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Generate a full AI investigation report for a case."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    case_result = await db.execute(
        select(Case).where(Case.id == body.case_id, Case.investigator_id == user_id)
    )
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    context = await _build_context(body.case_id, db)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Generate a professional digital forensics investigation report for:

Case: {case.title}
Description: {case.description}

Evidence Timeline:
{context}

Report Format:
1. Executive Summary
2. Investigation Scope
3. Key Findings
4. Suspicious Activities Detected
5. Attack Timeline Reconstruction
6. Root Cause Analysis
7. Risk Assessment
8. Recommendations
9. Conclusion"""

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

        report_content = response.choices[0].message.content

        # Save to DB
        ai_report = AIReport(
            case_id=body.case_id,
            summary=report_content[:500],
            risk_level="medium",
        )
        db.add(ai_report)
        await db.flush()

        return {"case_id": body.case_id, "report": report_content, "report_id": ai_report.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/chat")
async def get_chat_history(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get AI report history for a case."""
    result = await db.execute(
        select(AIReport).join(Case).where(
            AIReport.case_id == case_id, Case.investigator_id == user_id
        ).order_by(AIReport.generated_at.desc())
    )
    return result.scalars().all()
