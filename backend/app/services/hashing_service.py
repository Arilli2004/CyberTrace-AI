"""
Cryptographic Hashing Service — Streamed SHA-256, SHA-1, MD5
"""
import hashlib
from typing import Dict, Tuple, BinaryIO


class HashingService:
    CHUNK_SIZE = 64 * 1024  # 64 KB chunks

    @classmethod
    def calculate_file_hashes(cls, file_stream: BinaryIO) -> Tuple[Dict[str, str], int]:
        """
        Calculate SHA-256, SHA-1, and MD5 hashes in a single streaming pass.
        Returns dictionary of hashes and total size in bytes.
        """
        sha256_hash = hashlib.sha256()
        sha1_hash = hashlib.sha1()
        md5_hash = hashlib.md5()
        total_bytes = 0

        file_stream.seek(0)
        while chunk := file_stream.read(cls.CHUNK_SIZE):
            sha256_hash.update(chunk)
            sha1_hash.update(chunk)
            md5_hash.update(chunk)
            total_bytes += len(chunk)

        file_stream.seek(0)  # Reset stream position after hashing

        hashes = {
            "sha256": sha256_hash.hexdigest(),
            "sha1": sha1_hash.hexdigest(),
            "md5": md5_hash.hexdigest(),
        }
        return hashes, total_bytes
