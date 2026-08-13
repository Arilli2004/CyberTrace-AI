"""
AI API — LLM-powered investigation assistant & report generation (Gemma AI & LM Studio)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import httpx

from app.database.connection import get_db
from app.models import Case, Event, Evidence, AIReport, GraphNode
from app.core.security import get_current_user_id
from app.core.config import settings

router = APIRouter()


class AnalyzeRequest(BaseModel):
    case_id: int
    question: Optional[str] = None


class ReportRequest(BaseModel):
    case_id: int
    report_type: str = "full"  # full | summary | executive


async def _get_active_model_name(base_url: str) -> str:
    """Fetch active model name from LM Studio endpoint or fallback to settings."""
    try:
        models_url = f"{base_url.rstrip('/')}/models"
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(models_url)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["id"]
    except Exception:
        pass
    return getattr(settings, "OPENAI_MODEL", "google/gemma-4-e4b")


async def _build_context(case_id: int, db: AsyncSession) -> str:
    """Build comprehensive investigation context from case metadata, evidence, events, and graph nodes."""
    # 1. Case Details
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    
    context_sections = []
    if case:
        context_sections.append(
            f"=== CASE METADATA ===\n"
            f"Case ID: #{case.id}\n"
            f"Title: {case.title}\n"
            f"Description: {case.description}\n"
            f"Priority: {case.priority}\n"
            f"Status: {case.status}\n"
        )

    # 2. Uploaded Evidence Files
    ev_result = await db.execute(
        select(Evidence).where(Evidence.case_id == case_id, Evidence.is_deleted == False)
    )
    evidence_list = ev_result.scalars().all()
    if evidence_list:
        ev_lines = [f"- File: {e.original_filename} (Type: {e.file_type}, Size: {e.size} bytes, Parsed: {e.is_parsed})" for e in evidence_list]
        context_sections.append("=== UPLOADED EVIDENCE ===\n" + "\n".join(ev_lines) + "\n")

    # 3. Knowledge Graph Nodes
    graph_result = await db.execute(
        select(GraphNode).where(GraphNode.case_id == case_id).limit(50)
    )
    nodes = graph_result.scalars().all()
    if nodes:
        node_lines = [f"- Entity [{n.node_type}]: {n.node_label}" for n in nodes]
        context_sections.append("=== KNOWLEDGE GRAPH ENTITIES ===\n" + "\n".join(node_lines) + "\n")

    # 4. Events Timeline
    events_query = (
        select(Event)
        .where(Event.case_id == case_id)
        .order_by(Event.timestamp)
        .limit(200)
    )
    events_result = await db.execute(events_query)
    events = events_result.scalars().all()

    if events:
        evt_lines = [
            f"[{e.timestamp}] [{e.severity}] {e.event_type} | User: {e.user} | Host: {e.host} | {e.description}"
            for e in events
        ]
        context_sections.append("=== EVIDENCE TIMELINE ===\n" + "\n".join(evt_lines))
    else:
        context_sections.append("=== EVIDENCE TIMELINE ===\n(No parsed events recorded yet in timeline)")

    return "\n\n".join(context_sections)


@router.post("/analyze")
async def analyze_case(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """AI-powered analysis of a case using local Gemma AI (LM Studio) or OpenAI API."""
    case_result = await db.execute(
        select(Case).where(Case.id == body.case_id)
    )
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    context = await _build_context(body.case_id, db)
    base_url = getattr(settings, "OPENAI_BASE_URL", "http://127.0.0.1:1234/v1") or "http://127.0.0.1:1234/v1"
    api_key = getattr(settings, "OPENAI_API_KEY", "lm-studio") or "lm-studio"
    if "sk-your" in api_key or not api_key:
        api_key = "lm-studio"
    model_name = await _get_active_model_name(base_url)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(base_url=base_url, api_key=api_key)

        system_prompt = """You are Gemma AI — an expert digital forensics AI assistant integrated into CyberTrace AI.
You are provided with real evidence context from the user's active case (including case metadata, evidence files, extracted timeline events, and knowledge graph entities).

Your task:
1. Answer the investigator's question directly, accurately, and factual based ON THE GIVEN CASE CONTEXT.
2. If the user asks for suspicious activities, summarize exact key events, compromised hosts/users, and severity levels.
3. Structure your response clearly using Markdown formatting with bullet points and bold headers.
4. Be precise, professional, and forensic-minded."""

        user_message = f"ACTIVE CASE DETAILS:\n{context}\n\n"
        if body.question and body.question.strip():
            user_message += f"INVESTIGATOR QUESTION: {body.question.strip()}"
        else:
            user_message += "INVESTIGATOR REQUEST: Provide a full digital forensics assessment and findings summary for this case."

        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=getattr(settings, "OPENAI_MAX_TOKENS", 4096),
        )

        analysis = response.choices[0].message.content
        return {"case_id": body.case_id, "analysis": analysis, "model": model_name}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemma AI / LM Studio connection failed at {base_url}: {str(e)}. Make sure LM Studio is running on port 1234."
        )


@router.post("/report")
async def generate_report(
    body: ReportRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Generate a full AI investigation report for a case using Gemma AI."""
    case_result = await db.execute(
        select(Case).where(Case.id == body.case_id)
    )
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    context = await _build_context(body.case_id, db)
    base_url = getattr(settings, "OPENAI_BASE_URL", "http://127.0.0.1:1234/v1") or "http://127.0.0.1:1234/v1"
    api_key = getattr(settings, "OPENAI_API_KEY", "lm-studio") or "lm-studio"
    if "sk-your" in api_key or not api_key:
        api_key = "lm-studio"
    model_name = await _get_active_model_name(base_url)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(base_url=base_url, api_key=api_key)

        prompt = f"""Generate a comprehensive, formal Digital Forensics Investigation Report based on the following case data:

{context}

Please structure the report with these formal sections:
1. Executive Summary
2. Case Scope & Artifact Details
3. Reconstructed Attack Path & Key Findings
4. Suspicious & Anomalous Activities
5. Threat Severity & Risk Assessment
6. Incident Response & Containment Recommendations
7. Conclusion & Forensics Sign-off"""

        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=getattr(settings, "OPENAI_MAX_TOKENS", 4096),
        )

        report_content = response.choices[0].message.content

        # Save report record to DB
        ai_report = AIReport(
            case_id=body.case_id,
            summary=report_content[:500],
            risk_level=case.priority or "medium",
        )
        db.add(ai_report)
        await db.flush()

        return {"case_id": body.case_id, "report": report_content, "report_id": ai_report.id, "model": model_name}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemma AI report generation failed: {str(e)}"
        )


@router.get("/chat")
async def get_chat_history(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Get AI report history for a case."""
    result = await db.execute(
        select(AIReport).where(AIReport.case_id == case_id).order_by(AIReport.generated_at.desc())
    )
    return result.scalars().all()
