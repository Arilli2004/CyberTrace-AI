"""
Evidence Schemas — Pydantic V2 Request & Response Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from app.models import EvidenceType, ProcessingStage


class EvidenceUpdateSchema(BaseModel):
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = Field(None, max_length=20)
    verification_status: Optional[str] = Field(None, pattern="^(verified|pending|failed|tampered)$")


class ChainOfCustodyLogResponseSchema(BaseModel):
    id: int
    uuid_id: str
    evidence_id: int
    user_id: Optional[int] = None
    action: str
    details: Optional[Any] = None
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceResponseSchema(BaseModel):
    id: int
    uuid_id: Optional[str] = None
    case_id: int
    filename: str
    original_filename: str
    storage_path: str
    extension: str
    mime_type: str
    size: int
    sha256: str
    sha1: Optional[str] = None
    md5: Optional[str] = None
    file_type: EvidenceType
    uploaded_by: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    parser_status: str
    verification_status: str
    normalization_status: str
    graph_status: str
    csp_status: str
    correlation_status: str
    timeline_status: str
    ai_ready: bool
    processing_stage: ProcessingStage
    description: Optional[str] = None
    tags: Optional[Any] = None
    chain_of_custody_status: str
    is_parsed: bool
    parse_status: str
    event_count: int
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponseSchema(BaseModel):
    evidence: List[EvidenceResponseSchema]
    total: int
    skip: int
    limit: int
