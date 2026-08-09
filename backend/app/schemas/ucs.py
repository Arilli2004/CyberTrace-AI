"""
Pydantic V2 Schemas for Uniform Cost Search (UCS) Engine
Module 8 — Digital Forensics Optimal Attack Path Reconstruction
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class UCSRequest(BaseModel):
    """
    Request payload for executing Uniform Cost Search on a Knowledge Graph.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "case_id": 1,
                "start_node": "login",
                "goal_node": "usb_remove"
            }
        }
    )

    case_id: int = Field(..., description="ID of the investigation case", gt=0)
    start_node: str = Field(..., description="Starting event node label or ID", min_length=1)
    goal_node: str = Field(..., description="Destination event node label or ID", min_length=1)


class UCSResponse(BaseModel):
    """
    Response model returning the optimal path and execution metrics.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "path": [
                    "login",
                    "usb_insert",
                    "file_copy",
                    "usb_remove"
                ],
                "total_cost": 4.0,
                "visited_nodes": 7,
                "execution_time_ms": 12.5
            }
        }
    )

    success: bool = Field(..., description="Whether search succeeded in finding an optimal path")
    path: List[str] = Field(default_factory=list, description="Ordered sequence of node labels from start to goal")
    total_cost: float = Field(..., description="Cumulative minimum weight cost of the optimal path")
    visited_nodes: int = Field(..., description="Total number of graph nodes explored during search")
    execution_time_ms: float = Field(..., description="Execution duration in milliseconds")
    explanation: Optional[str] = Field(None, description="Detailed explanation of the search output")
