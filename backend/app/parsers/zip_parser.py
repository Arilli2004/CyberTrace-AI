"""
Zip Archive Parser — Archive Unpacker & inner File Dispatcher
"""
import zipfile
import tempfile
import os
import shutil
from typing import List, Dict, Any

from app.parsers.base_parser import BaseParser


class ZipParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        events = []
        temp_dir = tempfile.mkdtemp(prefix="cybertrace_unzip_")

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Zip bomb prevention: check total unpacked size
                total_unpacked_size = sum(file.file_size for file in zip_ref.infolist())
                if total_unpacked_size > 500 * 1024 * 1024:  # 500 MB limit
                    print(f"Zip bomb safety triggered for {file_path}")
                    return events

                zip_ref.extractall(temp_dir)

            from app.parsers.parser_factory import ParserFactory

            for root, _, files in os.walk(temp_dir):
                for filename in files:
                    inner_path = os.path.join(root, filename)
                    ext = filename.split(".")[-1].lower() if "." in filename else ""
                    if ext in ("exe", "dll", "bat", "sh", "ps1"):
                        continue  # Skip executables inside zip

                    parser = ParserFactory.get_parser_for_file(inner_path)
                    if parser and not isinstance(parser, ZipParser):
                        parsed_inner = parser.parse(inner_path)
                        events.extend(parsed_inner)

        except Exception as e:
            print(f"ZipParser Error on {file_path}: {e}")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return events
