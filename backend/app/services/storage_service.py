"""
Secure File Storage Service — Forensic Directory Management
"""
import os
import uuid
import shutil
from typing import BinaryIO, Tuple
from app.core.config import settings


class StorageService:
    def __init__(self, upload_base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = os.path.abspath(upload_base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_evidence_file(self, case_id: int, file_stream: BinaryIO, extension: str) -> Tuple[str, str, str]:
        """
        Safely store an evidence file under ./uploads/{case_id}/{uuid}.{ext}.
        Returns (internal_filename, absolute_storage_path, uuid_id).
        """
        case_dir = os.path.abspath(os.path.join(self.base_dir, str(case_id)))
        os.makedirs(case_dir, exist_ok=True)

        file_uuid = str(uuid.uuid4())
        safe_ext = extension.lstrip(".").lower() or "log"
        internal_filename = f"{file_uuid}.{safe_ext}"
        storage_path = os.path.abspath(os.path.join(case_dir, internal_filename))

        # Prevent Directory Traversal Attack
        if not storage_path.startswith(self.base_dir):
            raise ValueError("Security Error: Invalid storage path detected.")

        file_stream.seek(0)
        with open(storage_path, "wb") as dst:
            shutil.copyfileobj(file_stream, dst)

        return internal_filename, storage_path, file_uuid

    def delete_evidence_file(self, storage_path: str) -> bool:
        """Remove file from storage safely."""
        try:
            abs_path = os.path.abspath(storage_path)
            if abs_path.startswith(self.base_dir) and os.path.exists(abs_path):
                os.remove(abs_path)
                return True
        except Exception:
            pass
        return False
