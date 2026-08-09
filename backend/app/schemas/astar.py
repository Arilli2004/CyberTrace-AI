"""
Pydantic V2 Schemas for A* Search Engine
Module 9 — Digital Forensics Optimal Attack Path Reconstruction
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class AStarRequest(BaseModel):
    """
    Request payload for executing A* Search on a Knowledge Graph.
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


class AStarResponse(BaseModel):
    """
    Response model returning optimal path, total cost, heuristic cost, and execution metrics.
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
                "heuristic_cost": 2.0,
                "visited_nodes": 5,
                "execution_time_ms": 8.0,
                "explanation": "Optimal path found via A* Search with total cost 4.0 and initial heuristic 2.0."
            }
        }
    )

    success: bool = Field(..., description="Whether search succeeded in finding an optimal path")
    path: List[str] = Field(default_factory=list, description="Ordered sequence of node labels from start to goal")
    total_cost: float = Field(..., description="Cumulative minimum weight cost of the optimal path")
    heuristic_cost: float = Field(0.0, description="Initial estimated heuristic cost h(start, goal)")
    visited_nodes: int = Field(..., description="Total number of graph nodes explored during search")
    execution_time_ms: float = Field(..., description="Execution duration in milliseconds")
    explanation: Optional[str] = Field(None, description="Detailed explanation of the search output")
