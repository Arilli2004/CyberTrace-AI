"""
CSP API Router — Constraint Satisfaction & Backtracking Engine Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from app.database.connection import get_db
from app.services.csp_service import CSPService
from app.schemas.csp import (
    CSPStatusSchema,
    CSPResultsResponseSchema,
    GraphViolationSchema,
)
from app.core.security import get_current_user_id

router = APIRouter()


def get_csp_service(db: AsyncSession = Depends(get_db)) -> CSPService:
    return CSPService(db)


@router.post(
    "/csp/validate/{case_id}",
    response_model=CSPStatusSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Validate Knowledge Graph with CSP Backtracking",
    description="Execute Constraint Satisfaction Problem solver with recursive backtracking over Case Knowledge Graph.",
)
async def validate_case_graph(
    case_id: int,
    service: CSPService = Depends(get_csp_service),
    user_id: int = Depends(get_current_user_id),
):
    res = await service.validate_case_graph(case_id=case_id, user_id=user_id)
    return {
        "case_id": res["case_id"],
        "validation_status": res["validation_status"],
        "validation_score": res["validation_score"],
        "violations_count": res["violations_count"],
        "resolved_count": res["resolved_count"],
        "confidence_score": res["confidence_score"],
    }


@router.get(
    "/csp/status/{case_id}",
    response_model=CSPStatusSchema,
    summary="Get CSP Validation Status",
    description="Query current CSP validation status and latest validation score.",
)
async def get_validation_status(
    case_id: int,
    service: CSPService = Depends(get_csp_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_validation_status(case_id=case_id)


@router.get(
    "/csp/results/{case_id}",
    response_model=CSPResultsResponseSchema,
    summary="Get Detailed Validation Results",
    description="Retrieve comprehensive CSP validation run result, violations, and backtracking resolutions.",
)
async def get_validation_results(
    case_id: int,
    service: CSPService = Depends(get_csp_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_validation_results(case_id=case_id)


@router.get(
    "/csp/violations/{case_id}",
    response_model=List[GraphViolationSchema],
    summary="Get Graph Violations & Resolutions",
    description="Fetch list of constraint violations and backtracking resolution details for a case.",
)
async def get_violations(
    case_id: int,
    service: CSPService = Depends(get_csp_service),
    user_id: int = Depends(get_current_user_id),
):
    res = await service.get_validation_results(case_id=case_id)
    return res["violations"]
