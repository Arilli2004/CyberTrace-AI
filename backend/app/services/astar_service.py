"""
A* Service Layer — CyberTrace AI
Module 9 — Digital Forensics Optimal Attack Path Reconstruction

Coordinates Knowledge Graph loading, node/case validation, pluggable A* Search execution,
logging, and error handling.
"""
import logging
from typing import Dict, List, Tuple, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Case, GraphNode, GraphEdge
from app.ai.astar_search import AStarSearch, AStarResult, HopDistanceHeuristic, BaseHeuristic
from app.schemas.astar import AStarRequest, AStarResponse

logger = logging.getLogger(__name__)


class AStarService:
    """
    Service class providing high-level execution of A* Search on PostgreSQL-backed Knowledge Graphs.
    """

    def __init__(self, db: AsyncSession, custom_heuristic: BaseHeuristic = None):
        self.db = db
        self.heuristic = custom_heuristic or HopDistanceHeuristic()

    async def run_astar(self, request: AStarRequest) -> AStarResponse:
        """
        Loads Knowledge Graph for the specified case, executes A* Search, and returns structured path analysis.

        Args:
            request: AStarRequest schema containing case_id, start_node, and goal_node.

        Returns:
            AStarResponse containing path, total cost, heuristic cost, visited nodes, and execution time.

        Raises:
            HTTPException 404: Case or Start/Goal node not found in Knowledge Graph.
            HTTPException 400: No valid path exists between start and goal nodes.
        """
        # 1. Validate Case Existence
        case_stmt = select(Case).where(Case.id == request.case_id, Case.is_deleted == False)
        case_res = await self.db.execute(case_stmt)
        case = case_res.scalar_one_or_none()
        if not case:
            logger.warning("A* Search failed: Case ID %s not found.", request.case_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {request.case_id} not found."
            )

        # 2. Fetch Knowledge Graph Nodes for Case
        nodes_stmt = select(GraphNode).where(GraphNode.case_id == request.case_id)
        nodes_res = await self.db.execute(nodes_stmt)
        nodes: List[GraphNode] = list(nodes_res.scalars().all())

        if not nodes:
            logger.warning("A* Search failed: Knowledge Graph empty for Case ID %s.", request.case_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge Graph is empty for Case ID {request.case_id}."
            )

        # Build mapping of node labels and string IDs
        node_labels = {n.node_label for n in nodes}
        node_id_to_label = {n.id: n.node_label for n in nodes}
        node_str_ids = {str(n.id) for n in nodes}

        # Node properties dictionary for heuristic evaluations
        node_properties: Dict[str, Any] = {}
        for n in nodes:
            props = n.properties or {}
            node_properties[n.node_label] = props

        # Resolve start_node and goal_node identifiers
        start_label = self._resolve_node_label(request.start_node, node_labels, node_id_to_label, node_str_ids)
        if not start_label:
            logger.warning("A* Search failed: Start node '%s' not found in Case %s.", request.start_node, request.case_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Start node '{request.start_node}' not found in Knowledge Graph for Case ID {request.case_id}."
            )

        goal_label = self._resolve_node_label(request.goal_node, node_labels, node_id_to_label, node_str_ids)
        if not goal_label:
            logger.warning("A* Search failed: Goal node '%s' not found in Case %s.", request.goal_node, request.case_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal node '{request.goal_node}' not found in Knowledge Graph for Case ID {request.case_id}."
            )

        # 3. Fetch Knowledge Graph Edges for Case
        edges_stmt = select(GraphEdge).where(GraphEdge.case_id == request.case_id)
        edges_res = await self.db.execute(edges_stmt)
        edges: List[GraphEdge] = list(edges_res.scalars().all())

        # 4. Construct Adjacency List
        adjacency_list: Dict[str, List[Tuple[str, float]]] = {n.node_label: [] for n in nodes}
        for e in edges:
            src_label = node_id_to_label.get(e.source_node_id)
            dst_label = node_id_to_label.get(e.destination_node_id)
            if src_label and dst_label:
                weight = float(e.weight) if e.weight is not None else 1.0
                adjacency_list[src_label].append((dst_label, weight))

        # 5. Execute A* Search Engine
        logger.info(
            "Executing A* Search for Case ID %d | Start: '%s' | Goal: '%s'",
            request.case_id, start_label, goal_label
        )

        engine = AStarSearch(adjacency_list, heuristic=self.heuristic, node_properties=node_properties)
        result: AStarResult = engine.search(start_label, goal_label)

        # 6. Handle Path Not Found
        if not result.is_path_found:
            logger.warning(
                "A* Search completed: No path found between '%s' and '%s' in Case ID %d. Visited %d nodes.",
                start_label, goal_label, request.case_id, result.visited_nodes_count
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No valid path exists between start_node '{request.start_node}' and goal_node '{request.goal_node}' in Case ID {request.case_id}."
            )

        # 7. Log Execution Summary
        logger.info(
            "A* Search Succeeded | Case ID: %d | Start: '%s' | Goal: '%s' | Visited Nodes: %d | Total Cost: %.4f | Heuristic Cost: %.4f | Time: %.3f ms",
            request.case_id, start_label, goal_label, result.visited_nodes_count, result.total_cost, result.heuristic_cost, result.execution_time_ms
        )

        # 8. Return Structured Response
        return AStarResponse(
            success=True,
            path=result.path,
            total_cost=result.total_cost,
            heuristic_cost=result.heuristic_cost,
            visited_nodes=result.visited_nodes_count,
            execution_time_ms=result.execution_time_ms,
            explanation=result.explanation
        )

    @staticmethod
    def _resolve_node_label(
        identifier: str,
        labels: set,
        id_map: Dict[int, str],
        str_ids: set
    ) -> str:
        """Helper to match node by exact label or string numeric ID."""
        if identifier in labels:
            return identifier
        if identifier in str_ids:
            return id_map.get(int(identifier), "")
        return ""
