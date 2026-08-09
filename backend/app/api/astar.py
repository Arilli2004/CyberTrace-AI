"""
FastAPI Router for A* Search Engine
Module 9 — Digital Forensics Optimal Attack Path Reconstruction
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.astar import AStarRequest, AStarResponse
from app.services.astar_service import AStarService

router = APIRouter()


@router.post(
    "/run",
    response_model=AStarResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute A* Search on Case Knowledge Graph",
    description=(
        "Finds the optimal investigation evidence path between start_node and goal_node "
        "using heuristic-guided A* search over a validated Knowledge Graph."
    ),
    responses={
        200: {"description": "Optimal heuristic-guided path found successfully"},
        400: {"description": "No valid path exists between start and goal nodes"},
        404: {"description": "Case or Start/Goal node not found in Knowledge Graph"},
        422: {"description": "Validation error in payload parameters"},
    }
)
async def run_astar_search(
    body: AStarRequest,
    db: AsyncSession = Depends(get_db),
) -> AStarResponse:
    """
    POST /api/v1/ai/astar/run

    Executes A* Search for heuristic-guided evidence trajectory reconstruction.
    """
    service = AStarService(db)
    return await service.run_astar(body)
