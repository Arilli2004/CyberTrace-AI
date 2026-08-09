"""
Graph API Router — Enterprise Evidence Knowledge Graph Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from app.database.connection import get_db
from app.services.graph_service import GraphService
from app.repositories.graph_repository import GraphRepository
from app.schemas.graph import (
    GraphBuildStatusSchema,
    GraphPayloadSchema,
    GraphMetadataSchema,
)
from app.core.security import get_current_user_id

router = APIRouter()


def get_graph_service(db: AsyncSession = Depends(get_db)) -> GraphService:
    return GraphService(db)


def get_graph_repo(db: AsyncSession = Depends(get_db)) -> GraphRepository:
    return GraphRepository(db)


@router.post(
    "/graph/build/{case_id}",
    response_model=GraphBuildStatusSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Build Case Knowledge Graph",
    description="Construct Evidence Knowledge Graph from normalized events for a case.",
)
async def build_case_graph(
    case_id: int,
    service: GraphService = Depends(get_graph_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.build_case_graph(case_id=case_id, user_id=user_id)


@router.post(
    "/graph/build/evidence/{evidence_id}",
    response_model=GraphBuildStatusSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Build Evidence Knowledge Graph",
    description="Construct Knowledge Graph for a specific evidence file.",
)
async def build_evidence_graph(
    evidence_id: int,
    service: GraphService = Depends(get_graph_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.build_evidence_graph(evidence_id=evidence_id, user_id=user_id)


@router.get(
    "/graph/{case_id}",
    response_model=GraphPayloadSchema,
    summary="Get Full Case Knowledge Graph",
    description="Retrieve complete visual network graph topology (nodes + weighted edges) for interactive rendering.",
)
async def get_case_graph(
    case_id: int,
    service: GraphService = Depends(get_graph_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_case_graph(case_id=case_id)


@router.get(
    "/graph/statistics/{case_id}",
    response_model=GraphMetadataSchema,
    summary="Get Graph Metrics",
    description="Retrieve graph topological metrics (node count, edge count, density, components).",
)
async def get_graph_statistics(
    case_id: int,
    service: GraphService = Depends(get_graph_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_graph_statistics(case_id=case_id)


@router.delete(
    "/graph/{case_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Case Knowledge Graph",
    description="Clear Knowledge Graph nodes, edges, and metadata for a case.",
)
async def delete_case_graph(
    case_id: int,
    repo: GraphRepository = Depends(get_graph_repo),
    user_id: int = Depends(get_current_user_id),
):
    await repo.delete_graph_for_case(case_id=case_id)
    return {"message": f"Knowledge Graph for case #{case_id} deleted successfully."}
