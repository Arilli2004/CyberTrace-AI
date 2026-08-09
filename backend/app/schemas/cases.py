"""
Case Schemas — Pydantic V2 Request & Response Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models import CaseStatus


class CaseCreateSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Title of the investigation case")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed case description")
    priority: str = Field("medium", pattern="^(low|medium|high|critical)$", description="Case priority level")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Ransomware Outbreak - Workstation WS-04",
                "description": "Suspected WannaCry variant detected on finance workstation.",
                "priority": "critical",
            }
        }
    )


class CaseUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[CaseStatus] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")


class CaseResponseSchema(BaseModel):
    id: int
    uuid_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    investigator_id: int
    status: CaseStatus
    priority: str
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CaseListResponseSchema(BaseModel):
    cases: List[CaseResponseSchema]
    total: int
    skip: int
    limit: int
