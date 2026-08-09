"""
Evidence Service — Core Business Logic & Ingestion Orchestrator
"""
from typing import Optional, List, Tuple
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.repositories.evidence_repository import EvidenceRepository
from app.services.storage_service import StorageService
from app.services.hashing_service import HashingService
from app.utils.validators import validate_evidence_file, sanitize_filename
from app.schemas.evidence import EvidenceUpdateSchema
from app.models import Evidence, EvidenceType, ChainOfCustodyLog


class EvidenceService:
    def __init__(self, db: AsyncSession):
        self.repository = EvidenceRepository(db)
        self.storage = StorageService()

    def _map_extension_to_evidence_type(self, ext: str) -> EvidenceType:
        ext_map = {
            "evtx": EvidenceType.evtx,
            "log": EvidenceType.log,
            "csv": EvidenceType.csv,
            "json": EvidenceType.json,
            "xml": EvidenceType.xml,
            "txt": EvidenceType.txt,
            "zip": EvidenceType.zip,
        }
        return ext_map.get(ext.lower(), EvidenceType.log)

    async def upload_evidence(self, case_id: int, user_id: int, files: List[UploadFile]) -> List[Evidence]:
        """Ingest, validate, hash, store, and record Chain of Custody for uploaded files."""
        uploaded_records = []

        for file in files:
            ext, mime_type = validate_evidence_file(file)
            original_filename = sanitize_filename(file.filename or "evidence.log")

            # Calculate SHA256, SHA1, MD5 hashes
            hashes, total_size = HashingService.calculate_file_hashes(file.file)

            # Duplicate Hash Prevention within the case
            existing = await self.repository.get_by_sha256_in_case(case_id, hashes["sha256"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Duplicate Evidence Error: File '{original_filename}' (SHA-256: {hashes['sha256'][:12]}...) has already been uploaded to Case #{case_id}.",
                )

            # Save file to storage
            internal_filename, storage_path, file_uuid = self.storage.save_evidence_file(
                case_id=case_id,
                file_stream=file.file,
                extension=ext,
            )

            # Create DB record
            evidence = Evidence(
                uuid_id=file_uuid,
                case_id=case_id,
                filename=internal_filename,
                original_filename=original_filename,
                storage_path=storage_path,
                file_path=storage_path,
                extension=ext,
                mime_type=mime_type,
                size=total_size,
                sha256=hashes["sha256"],
                sha1=hashes["sha1"],
                md5=hashes["md5"],
                file_type=self._map_extension_to_evidence_type(ext),
                uploaded_by=user_id,
                verification_status="verified",
                normalization_status="pending",
                graph_status="pending",
                csp_status="pending",
                correlation_status="pending",
                timeline_status="pending",
                ai_ready=False,
                processing_stage="VERIFIED",
                chain_of_custody_status="intact",
                parser_status="pending",
                is_parsed=False,
                is_deleted=False,
            )

            record = await self.repository.create(evidence)

            # Record Chain of Custody Audit Log
            await self.repository.log_custody_action(
                evidence_id=record.id,
                user_id=user_id,
                action="UPLOAD",
                details={
                    "original_filename": original_filename,
                    "sha256": hashes["sha256"],
                    "size_bytes": total_size,
                    "storage_path": storage_path,
                },
            )

            uploaded_records.append(record)

        return uploaded_records

    async def list_evidence(
        self,
        case_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        file_type: Optional[EvidenceType] = None,
    ) -> Tuple[List[Evidence], int]:
        return await self.repository.list_evidence(
            case_id=case_id, skip=skip, limit=limit, search=search, file_type=file_type
        )

    async def get_evidence_by_id(self, evidence_id: int) -> Evidence:
        record = await self.repository.get_by_id(evidence_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence record with ID {evidence_id} not found.",
            )
        return record

    async def update_evidence(self, evidence_id: int, user_id: int, data: EvidenceUpdateSchema) -> Evidence:
        record = await self.get_evidence_by_id(evidence_id)
        update_dict = data.model_dump(exclude_none=True)
        updated = await self.repository.update(record, update_dict)

        await self.repository.log_custody_action(
            evidence_id=record.id,
            user_id=user_id,
            action="UPDATED",
            details=update_dict,
        )

        return updated

    async def delete_evidence(self, evidence_id: int, user_id: int) -> None:
        record = await self.get_evidence_by_id(evidence_id)
        await self.repository.soft_delete(record)
        self.storage.delete_evidence_file(record.storage_path)

        await self.repository.log_custody_action(
            evidence_id=record.id,
            user_id=user_id,
            action="DELETED",
            details={"original_filename": record.original_filename, "sha256": record.sha256},
        )

    async def get_custody_logs(self, evidence_id: int) -> List[ChainOfCustodyLog]:
        await self.get_evidence_by_id(evidence_id)
        return await self.repository.get_custody_logs(evidence_id)
