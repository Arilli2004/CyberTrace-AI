"""
Evidence API Router — Digital Evidence Ingestion, Management & Stream Downloads
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os

from app.database.connection import get_db
from app.services.evidence_service import EvidenceService
from app.services.storage_service import StorageService
from app.schemas.evidence import (
    EvidenceResponseSchema,
    EvidenceListResponseSchema,
    EvidenceUpdateSchema,
    ChainOfCustodyLogResponseSchema,
)
from app.models import EvidenceType
from app.core.security import get_current_user_id

router = APIRouter()


def get_evidence_service(db: AsyncSession = Depends(get_db)) -> EvidenceService:
    return EvidenceService(db)


@router.get(
    "/",
    response_model=EvidenceListResponseSchema,
    summary="List Digital Evidence",
    description="Retrieve paginated list of evidence files across cases with optional search and type filtering.",
)
async def list_evidence(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by filename or SHA-256 hash"),
    file_type: Optional[EvidenceType] = Query(None, description="Filter by file type"),
    service: EvidenceService = Depends(get_evidence_service),
    user_id: int = Depends(get_current_user_id),
):
    evidence, total = await service.list_evidence(
        skip=skip, limit=limit, search=search, file_type=file_type
    )
    return {"evidence": evidence, "total": total, "skip": skip, "limit": limit}


@router.post(
    "/upload",
    response_model=List[EvidenceResponseSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Upload Forensic Evidence Files",
    description="Upload single or multiple forensic evidence log files (EVTX, Log, CSV, JSON, XML, TXT, ZIP) to a case.",
)
async def upload_evidence(
    case_id: int = Form(...),
    files: List[UploadFile] = File(...),
    service: EvidenceService = Depends(get_evidence_service),
    user_id: int = Depends(get_current_user_id),
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")
    return await service.upload_evidence(case_id=case_id, user_id=user_id, files=files)


@router.get(
    "/case/{case_id}",
    response_model=EvidenceListResponseSchema,
    summary="List Case Evidence",
    description="Retrieve all evidence files associated with a specific case ID.",
)
async def list_case_evidence(
    case_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: EvidenceService = Depends(get_evidence_service),
    user_id: int = Depends(get_current_user_id),
):
    evidence, total = await service.list_evidence(case_id=case_id, skip=skip, limit=limit)
    return {"evidence": evidence, "total": total, "skip": skip, "limit": limit}


@router.get(
    "/{id}",
    response_model=EvidenceResponseSchema,
    summary="Get Evidence Details",
    description="Retrieve metadata and cryptographic hash verification details for an evidence file.",
)
async def get_evidence(
    id: int,
    service: EvidenceService = Depends(get_evidence_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_evidence_by_id(evidence_id=id)


@router.patch(
    "/{id}",
    response_model=EvidenceResponseSchema,
    summary="Update Evidence Metadata",
    description="Update tags, description, or verification status of an evidence file.",
)
async def update_evidence(
    id: int,
    body: EvidenceUpdateSchema,
    service: EvidenceService = Depends(get_evidence_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.update_evidence(evidence_id=id, user_id=user_id, data=body)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft Delete Evidence File",
    description="Safely soft-delete evidence record and log deletion audit trail.",
)
async def delete_evidence(
    id: int,
    service: EvidenceService = Depends(get_evidence_service),
    user_id: int = Depends(get_current_user_id),
):
    await service.delete_evidence(evidence_id=id, user_id=user_id)


@router.get(
    "/download/{id}",
    summary="Download Evidence File",
    description="Stream download the original raw evidence file.",
)
async def download_evidence(
    id: int,
    service: EvidenceService = Depends(get_evidence_service),
    user_id: int = Depends(get_current_user_id),
):
    record = await service.get_evidence_by_id(evidence_id=id)
    storage_path = StorageService.resolve_file_path(record.storage_path)
    if not os.path.exists(storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File content not found on storage disk.",
        )

    # Log download action in Chain of Custody
    await service.repository.log_custody_action(
        evidence_id=record.id,
        user_id=user_id,
        action="DOWNLOADED",
        details={"original_filename": record.original_filename},
    )

    return FileResponse(
        path=storage_path,
        filename=record.original_filename,
        media_type=record.mime_type,
    )


@router.get(
    "/{id}/custody",
    response_model=List[ChainOfCustodyLogResponseSchema],
    summary="Get Chain of Custody Audit Trail",
    description="Retrieve full timestamped audit log of all actions performed on an evidence file.",
)
async def get_custody_logs(
    id: int,
    service: EvidenceService = Depends(get_evidence_service),
    user_id: int = Depends(get_current_user_id),
):
    return await service.get_custody_logs(evidence_id=id)
