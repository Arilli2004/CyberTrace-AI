"""
FastAPI Router for Uniform Cost Search (UCS) Engine
Module 8 — Digital Forensics Optimal Attack Path Reconstruction
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.ucs import UCSRequest, UCSResponse
from app.services.ucs_service import UCSService

router = APIRouter()


@router.post(
    "/run",
    response_model=UCSResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Uniform Cost Search on Case Knowledge Graph",
    description=(
        "Identifies the minimum-cost evidence path between start_node and goal_node "
        "within a validated Knowledge Graph for a specific investigation case."
    ),
    responses={
        200: {"description": "Optimal path found successfully"},
        400: {"description": "No valid path exists between start and goal nodes"},
        404: {"description": "Case or Start/Goal node not found in Knowledge Graph"},
        422: {"description": "Validation error in payload parameters"},
    }
)
async def run_uniform_cost_search(
    body: UCSRequest,
    db: AsyncSession = Depends(get_db),
) -> UCSResponse:
    """
    POST /api/v1/ai/ucs/run

    Executes Uniform Cost Search for optimal evidence trajectory reconstruction.
    """
    service = UCSService(db)
    return await service.run_ucs(body)
