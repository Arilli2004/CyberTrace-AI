"""
Graph Schemas — Pydantic V2 Request & Response Models for Knowledge Graph
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import ProcessingStage


class GraphNodeSchema(BaseModel):
    id: str
    uuid_id: str
    type: str
    label: str
    properties: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class GraphEdgeSchema(BaseModel):
    id: str
    uuid_id: str
    source: str
    target: str
    type: str
    weight: float
    confidence: float
    timestamp: Optional[str] = None
    properties: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class GraphMetadataSchema(BaseModel):
    case_id: int
    node_count: int
    edge_count: int
    density: float
    connected_components: int

    model_config = ConfigDict(from_attributes=True)


class GraphPayloadSchema(BaseModel):
    case_id: int
    nodes: List[GraphNodeSchema]
    edges: List[GraphEdgeSchema]
    metadata: GraphMetadataSchema


class GraphBuildStatusSchema(BaseModel):
    case_id: int
    status: str
    node_count: int
    edge_count: int
    processing_stage: ProcessingStage
