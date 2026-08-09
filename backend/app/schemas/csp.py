"""
CSP Schemas — Pydantic V2 Request & Response Models for Constraint Engine
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from app.models import ProcessingStage


class CSPStatusSchema(BaseModel):
    case_id: int
    validation_status: str
    validation_score: float
    violations_count: int
    resolved_count: int
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)


class GraphViolationSchema(BaseModel):
    id: int
    status: str
    violation_reason: Optional[str] = None
    resolution_details: Optional[str] = None
    confidence: float

    model_config = ConfigDict(from_attributes=True)


class CSPResultsResponseSchema(BaseModel):
    case_id: int
    result: CSPStatusSchema
    violations: List[GraphViolationSchema]
