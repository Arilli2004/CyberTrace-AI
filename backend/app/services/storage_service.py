"""
Secure File Storage Service — Forensic Directory Management
"""
import os
import uuid
import shutil
from typing import BinaryIO, Tuple
from app.core.config import settings


class StorageService:
    def __init__(self, upload_base_dir: str = None):
        self.base_dir = upload_base_dir or self.get_upload_base_dir()
        os.makedirs(self.base_dir, exist_ok=True)

    @classmethod
    def get_upload_base_dir(cls) -> str:
        """Get absolute path to backend upload directory reliably."""
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backend_dir = os.path.dirname(app_dir)
        uploads_dir = os.path.join(backend_dir, "uploads")
        if os.path.exists(uploads_dir):
            return os.path.abspath(uploads_dir)

        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "backend", "uploads")):
            return os.path.abspath(os.path.join(cwd, "backend", "uploads"))
        if os.path.exists(os.path.join(cwd, "uploads")):
            return os.path.abspath(os.path.join(cwd, "uploads"))

        return os.path.abspath(settings.UPLOAD_DIR or "./uploads")

    @classmethod
    def resolve_file_path(cls, file_path: str) -> str:
        """
        Dynamically resolve file_path if project directory location has moved or changed.
        Ensures evidence parsing succeeds even if absolute paths recorded in DB differ.
        """
        if not file_path:
            return file_path
        if os.path.exists(file_path):
            return os.path.abspath(file_path)

        base_uploads = cls.get_upload_base_dir()
        normalized = file_path.replace("\\", "/")

        # 1. Match relative path after "uploads/"
        if "uploads/" in normalized:
            rel = normalized.split("uploads/", 1)[1]
            resolved = os.path.abspath(os.path.join(base_uploads, rel.replace("/", os.sep)))
            if os.path.exists(resolved):
                return resolved

        # 2. Match case_id/filename (e.g. "3/22285a1f-edec-4b90-8dca-f4e3350ce653.csv")
        parts = [p for p in normalized.split("/") if p]
        if len(parts) >= 2:
            rel = os.path.join(parts[-2], parts[-1])
            resolved = os.path.abspath(os.path.join(base_uploads, rel))
            if os.path.exists(resolved):
                return resolved

        # 3. Match filename anywhere inside uploads/ directory recursively
        filename = os.path.basename(file_path)
        for root, _, files in os.walk(base_uploads):
            if filename in files:
                return os.path.abspath(os.path.join(root, filename))

        return file_path

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
