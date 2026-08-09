"""
Parser Factory — Dynamic Plugin Selection
"""
import os
from typing import Optional

from app.parsers.base_parser import BaseParser
from app.parsers.evtx_parser import EvtxParser
from app.parsers.linux_parser import LinuxParser
from app.parsers.csv_parser import CsvParser
from app.parsers.json_parser import JsonParser
from app.parsers.xml_parser import XmlParser
from app.parsers.txt_parser import TxtParser
from app.parsers.zip_parser import ZipParser


class ParserFactory:
    @classmethod
    def get_parser_for_file(cls, file_path: str, hint_extension: Optional[str] = None) -> BaseParser:
        """Select appropriate parser plugin based on file extension and path."""
        ext = (hint_extension or file_path.split(".")[-1]).lower()

        if ext == "evtx":
            return EvtxParser()
        elif ext == "csv":
            return CsvParser()
        elif ext == "json":
            return JsonParser()
        elif ext == "xml":
            return XmlParser()
        elif ext == "zip":
            return ZipParser()
        elif ext in ("log", "txt", "syslog"):
            # Inspect file header or filename for linux syslog
            filename = os.path.basename(file_path).lower()
            if "auth" in filename or "syslog" in filename or "messages" in filename:
                return LinuxParser()
            return TxtParser()
        else:
            return TxtParser()
