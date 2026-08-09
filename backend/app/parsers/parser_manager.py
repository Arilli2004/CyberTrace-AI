"""
Parser Manager — High-Level Ingestion Dispatcher & Async Execution
"""
import os
import asyncio
from typing import List, Dict, Any

from app.parsers.parser_factory import ParserFactory


class ParserManager:
    @classmethod
    def parse_file(cls, file_path: str, extension: str) -> List[Dict[str, Any]]:
        """Synchronously execute parsing using appropriate factory plugin."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Evidence file path '{file_path}' does not exist.")

        parser = ParserFactory.get_parser_for_file(file_path=file_path, hint_extension=extension)
        return parser.parse(file_path)

    @classmethod
    async def parse_file_async(cls, file_path: str, extension: str) -> List[Dict[str, Any]]:
        """Asynchronously execute parsing in a background thread worker pool."""
        return await asyncio.to_thread(cls.parse_file, file_path, extension)
