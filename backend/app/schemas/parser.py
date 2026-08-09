"""
Parser & Event Schemas — Pydantic V2 Request & Response Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from app.models import SeverityLevel, ProcessingStage


class ParserStatusSchema(BaseModel):
    evidence_id: int
    filename: Optional[str] = None
    parser_status: str
    processing_stage: ProcessingStage
    event_count: int
    is_parsed: bool

    model_config = ConfigDict(from_attributes=True)


class EventResponseSchema(BaseModel):
    id: int
    uuid_id: str
    evidence_id: int
    case_id: Optional[int] = None
    timestamp: datetime
    source: Optional[str] = None
    event_type: Optional[str] = None
    event_id: Optional[str] = None
    user: Optional[str] = None
    host: Optional[str] = None
    ip_address: Optional[str] = None
    process: Optional[str] = None
    file_path: Optional[str] = None
    severity: SeverityLevel
    description: Optional[str] = None
    raw_data: Optional[Any] = None
    is_suspicious: bool
    confidence_score: float
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EventListResponseSchema(BaseModel):
    events: List[EventResponseSchema]
    total: int
    skip: int
    limit: int
