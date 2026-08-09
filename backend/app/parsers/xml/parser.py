"""
XML Log Parser — CyberTrace AI
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


def parse_xml(file_path: str) -> List[Dict[str, Any]]:
    """Parse XML log files into normalized events."""
    events = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for elem in root:
            event = _normalize_xml_element(elem)
            events.append(event)
    except Exception as e:
        pass

    return events


def _normalize_xml_element(elem: ET.Element) -> Dict[str, Any]:
    data = {}
    for child in elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        data[tag.lower()] = child.text or ""

    return {
        "timestamp": data.get("timestamp") or data.get("time") or data.get("timecreated") or "",
        "source": "XML Log",
        "event_type": data.get("event_type") or data.get("eventid") or data.get("action") or elem.tag,
        "user": data.get("user") or data.get("username") or "",
        "host": data.get("host") or data.get("computer") or "",
        "ip_address": data.get("ip") or data.get("ipaddress") or "",
        "severity": data.get("severity") or "low",
        "description": data.get("description") or data.get("message") or f"XML element {elem.tag}",
        "raw_data": data,
    }
