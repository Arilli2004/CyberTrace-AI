"""
Graph Service — High-Level Knowledge Graph Service Orchestrator
"""
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.normalized_event_repository import NormalizedEventRepository
from app.repositories.graph_repository import GraphRepository
from app.graph.knowledge_graph_builder import KnowledgeGraphBuilder
from app.models import Evidence, ProcessingStage, GraphMetadata


class GraphService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.norm_event_repo = NormalizedEventRepository(db)
        self.graph_repo = GraphRepository(db)

    async def build_case_graph(self, case_id: int, user_id: int) -> Dict[str, Any]:
        """Build or rebuild complete Evidence Knowledge Graph for a case."""
        norm_events, total_events = await self.norm_event_repo.list_normalized_events_by_case(
            case_id=case_id, limit=10000
        )

        if not norm_events:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Case #{case_id} has 0 normalized events. Please normalize evidence first.",
            )

        # Clear existing graph
        await self.graph_repo.delete_graph_for_case(case_id=case_id)

        # Build Graph in thread pool
        nodes, edges, metadata = await asyncio.to_thread(
            KnowledgeGraphBuilder.build_graph, norm_events, case_id
        )

        # Persist Graph
        node_count, edge_count = await self.graph_repo.save_graph(nodes=nodes, edges=edges, metadata=metadata)

        # Update Evidence processing stage
        evidence_list, _ = await self.evidence_repo.list_evidence(case_id=case_id, limit=100)
        for e in evidence_list:
            if e.normalization_status == "completed":
                e.graph_status = "completed"
                e.processing_stage = ProcessingStage.GRAPH_CREATED
                # Log Chain of Custody Audit
                await self.evidence_repo.log_custody_action(
                    evidence_id=e.id,
                    user_id=user_id,
                    action="GRAPH_CREATE",
                    details={
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "processing_stage": "GRAPH_CREATED",
                    },
                )
        await self.db.flush()

        return {
            "case_id": case_id,
            "status": "completed",
            "node_count": node_count,
            "edge_count": edge_count,
            "processing_stage": "GRAPH_CREATED",
        }

    async def build_evidence_graph(self, evidence_id: int, user_id: int) -> Dict[str, Any]:
        """Build Knowledge Graph for a specific evidence file."""
        evidence = await self.evidence_repo.get_by_id(evidence_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence #{evidence_id} not found.")

        return await self.build_case_graph(case_id=evidence.case_id, user_id=user_id)

    async def get_case_graph(self, case_id: int) -> Dict[str, Any]:
        """Fetch complete visual network graph payload (nodes and edges)."""
        nodes, edges = await self.graph_repo.get_full_graph(case_id)
        metadata = await self.graph_repo.get_metadata(case_id)

        return {
            "case_id": case_id,
            "nodes": [
                {
                    "id": str(n.id),
                    "uuid_id": n.uuid_id,
                    "type": n.node_type,
                    "label": n.node_label,
                    "properties": n.properties or {},
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "uuid_id": e.uuid_id,
                    "source": str(e.source_node_id),
                    "target": str(e.destination_node_id),
                    "type": e.edge_type,
                    "weight": e.weight,
                    "confidence": e.confidence,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "properties": e.properties or {},
                }
                for e in edges
            ],
            "metadata": {
                "case_id": case_id,
                "node_count": metadata.node_count if metadata else len(nodes),
                "edge_count": metadata.edge_count if metadata else len(edges),
                "density": metadata.density if metadata else 0.0,
                "connected_components": metadata.connected_components if metadata else 1,
            },
        }

    async def get_graph_statistics(self, case_id: int) -> Dict[str, Any]:
        """Get summary graph metrics."""
        metadata = await self.graph_repo.get_metadata(case_id)
        if not metadata:
            return {
                "case_id": case_id,
                "node_count": 0,
                "edge_count": 0,
                "density": 0.0,
                "connected_components": 0,
            }
        return {
            "case_id": case_id,
            "node_count": metadata.node_count,
            "edge_count": metadata.edge_count,
            "density": metadata.density,
            "connected_components": metadata.connected_components,
        }
