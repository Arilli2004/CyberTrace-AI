"""
Graph Repository — Database Persistence & Query Access Layer
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional, List, Tuple, Dict, Any

from app.models import GraphNode, GraphEdge, GraphMetadata


class GraphRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_graph(self, nodes: List[GraphNode], edges: List[GraphEdge], metadata: GraphMetadata) -> Tuple[int, int]:
        """Save graph nodes, edges, and metadata into database."""
        # 1. Add nodes
        for i in range(0, len(nodes), 1000):
            chunk = nodes[i : i + 1000]
            self.db.add_all(chunk)
            await self.db.flush()

        # 2. Add edges
        for i in range(0, len(edges), 1000):
            chunk = edges[i : i + 1000]
            self.db.add_all(chunk)
            await self.db.flush()

        # 3. Add or update metadata
        existing_meta = await self.get_metadata(metadata.case_id)
        if existing_meta:
            existing_meta.node_count = metadata.node_count
            existing_meta.edge_count = metadata.edge_count
            existing_meta.connected_components = metadata.connected_components
            existing_meta.density = metadata.density
        else:
            self.db.add(metadata)
        await self.db.flush()

        return len(nodes), len(edges)

    async def delete_graph_for_case(self, case_id: int) -> None:
        """Clear existing graph nodes, edges, and metadata for a case."""
        await self.db.execute(delete(GraphEdge).where(GraphEdge.case_id == case_id))
        await self.db.execute(delete(GraphNode).where(GraphNode.case_id == case_id))
        await self.db.execute(delete(GraphMetadata).where(GraphMetadata.case_id == case_id))
        await self.db.flush()

    async def get_full_graph(self, case_id: int) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Fetch all nodes and edges for visual rendering."""
        node_res = await self.db.execute(select(GraphNode).where(GraphNode.case_id == case_id))
        nodes = node_res.scalars().all()

        edge_res = await self.db.execute(select(GraphEdge).where(GraphEdge.case_id == case_id))
        edges = edge_res.scalars().all()

        return list(nodes), list(edges)

    async def list_nodes(self, case_id: int, skip: int = 0, limit: int = 50, node_type: Optional[str] = None) -> Tuple[List[GraphNode], int]:
        """Fetch paginated graph nodes."""
        query = select(GraphNode).where(GraphNode.case_id == case_id)
        if node_type:
            query = query.where(GraphNode.node_type == node_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one() or 0

        query = query.order_by(GraphNode.id.asc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        nodes = result.scalars().all()

        return list(nodes), total

    async def list_edges(self, case_id: int, skip: int = 0, limit: int = 50, edge_type: Optional[str] = None) -> Tuple[List[GraphEdge], int]:
        """Fetch paginated graph edges."""
        query = select(GraphEdge).where(GraphEdge.case_id == case_id)
        if edge_type:
            query = query.where(GraphEdge.edge_type == edge_type)

        count_query = select(func.count()).select_from(query.subquery())
        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one() or 0

        query = query.order_by(GraphEdge.id.asc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        edges = result.scalars().all()

        return list(edges), total

    async def get_metadata(self, case_id: int) -> Optional[GraphMetadata]:
        result = await self.db.execute(select(GraphMetadata).where(GraphMetadata.case_id == case_id))
        return result.scalar_one_or_none()
