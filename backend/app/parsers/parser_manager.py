"""
Parser Manager — High-Level Ingestion Dispatcher & Async Execution
"""
import os
import asyncio
from typing import List, Dict, Any

from app.parsers.parser_factory import ParserFactory
from app.services.storage_service import StorageService


class ParserManager:
    @classmethod
    def parse_file(cls, file_path: str, extension: str) -> List[Dict[str, Any]]:
        """Synchronously execute parsing using appropriate factory plugin."""
        resolved_path = StorageService.resolve_file_path(file_path)
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"Evidence file path '{file_path}' does not exist on disk.")

        parser = ParserFactory.get_parser_for_file(file_path=resolved_path, hint_extension=extension)
        return parser.parse(resolved_path)

    @classmethod
    async def parse_file_async(cls, file_path: str, extension: str) -> List[Dict[str, Any]]:
        """Asynchronously execute parsing in a background thread worker pool."""
        return await asyncio.to_thread(cls.parse_file, file_path, extension)
