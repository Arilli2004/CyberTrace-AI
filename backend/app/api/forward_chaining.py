"""
FastAPI Router for Forward Chaining Inference Engine
Module 10 — Data-Driven Forensic Threat Reasoning
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.forward_chaining import ForwardChainingRequest, ForwardChainingResponse
from app.services.forward_chaining_service import ForwardChainingService

router = APIRouter()


@router.post(
    "/run",
    response_model=ForwardChainingResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Forward Chaining Threat Inference on Case Evidence",
    description=(
        "Evaluates known forensic facts against security rules to iteratively deduce "
        "new threat indicators, TTPs, and incident hypotheses using data-driven forward chaining."
    ),
    responses={
        200: {"description": "Threat inference completed successfully"},
        404: {"description": "Case not found"},
        422: {"description": "Validation error in payload parameters"},
    }
)
async def run_forward_chaining_inference(
    body: ForwardChainingRequest,
    db: AsyncSession = Depends(get_db),
) -> ForwardChainingResponse:
    """
    POST /api/v1/ai/forward-chaining/run

    Executes Forward Chaining inference over Case evidence facts.
    """
    service = ForwardChainingService(db)
    return await service.run_forward_chaining(body)
