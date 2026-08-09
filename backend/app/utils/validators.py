"""
Evidence File & Security Validators — CyberTrace AI
"""
import os
import re
from typing import Tuple
from fastapi import HTTPException, status, UploadFile

ALLOWED_EXTENSIONS = {"evtx", "log", "csv", "json", "xml", "txt", "zip"}
BLOCKED_EXTENSIONS = {
    "exe", "dll", "bat", "sh", "ps1", "vbs", "py", "js", "msi", "cmd",
    "com", "scr", "hta", "cpl", "jar", "vbe", "jse", "wsf", "wsh"
}
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and header injections."""
    clean = os.path.basename(filename)
    clean = re.sub(r'[^\w\.\-]', '_', clean)
    return clean.strip("_") or "evidence.log"


def validate_evidence_file(file: UploadFile) -> Tuple[str, str]:
    """
    Validate uploaded evidence file extension, type, and security constraints.
    Returns clean extension and MIME type.
    """
    filename = file.filename or ""
    clean_name = sanitize_filename(filename)

    ext = clean_name.split(".")[-1].lower() if "." in clean_name else ""

    # Check for blocked executable extensions
    if ext in BLOCKED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Error: Executable and script file types (.{ext}) are strictly prohibited.",
        )

    # Check for allowed extensions
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    mime_type = file.content_type or "application/octet-stream"
    return ext, mime_type
