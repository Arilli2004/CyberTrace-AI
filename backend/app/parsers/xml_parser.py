"""
XML Log Parser — CyberTrace AI
"""
from typing import List, Dict, Any
import xml.etree.ElementTree as ET

from app.parsers.base_parser import BaseParser


class XmlParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        events = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            for elem in root.iter():
                if len(elem) > 0:  # Leaf container or node
                    data = {child.tag: child.text for child in elem if child.text}
                    if data:
                        events.append(
                            self.create_event_dict(
                                source="XmlLog",
                                event_type=elem.tag,
                                description=f"XML node <{elem.tag}> parsed",
                                raw_event=data,
                            )
                        )

        except Exception as e:
            print(f"XmlParser Error on {file_path}: {e}")

        return events
