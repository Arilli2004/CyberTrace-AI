"""
Normalization Schemas — Pydantic V2 Request & Response Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from app.models import EventCategory, SeverityLevel, ProcessingStage


class NormalizationStatusSchema(BaseModel):
    evidence_id: int
    filename: Optional[str] = None
    normalization_status: str
    processing_stage: ProcessingStage
    event_count: int

    model_config = ConfigDict(from_attributes=True)


class NormalizedEventResponseSchema(BaseModel):
    id: int
    uuid_id: str
    event_id: Optional[int] = None
    case_id: int
    evidence_id: int
    timestamp_utc: datetime
    hostname: Optional[str] = None
    device_name: Optional[str] = None
    username: Optional[str] = None
    domain: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    process_name: Optional[str] = None
    process_id: Optional[str] = None
    parent_process: Optional[str] = None
    command_line: Optional[str] = None
    event_type: Optional[str] = None
    event_category: EventCategory
    severity: SeverityLevel
    action: str
    object_name: Optional[str] = None
    file_path: Optional[str] = None
    registry_key: Optional[str] = None
    network_protocol: Optional[str] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    source: Optional[str] = None
    confidence_score: float
    parser_source: Optional[str] = None
    raw_event_reference: Optional[Any] = None
    normalized: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NormalizedEventListResponseSchema(BaseModel):
    events: List[NormalizedEventResponseSchema]
    total: int
    skip: int
    limit: int
