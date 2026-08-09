"""
EVTX Parser — Parse Windows Event Log files (.evtx)
"""
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import xml.etree.ElementTree as ET

try:
    import Evtx.Evtx as evtx
    import Evtx.Views as e_views
    EVTX_AVAILABLE = True
except ImportError:
    EVTX_AVAILABLE = False


def parse_evtx(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a Windows EVTX file and return normalized events.

    Returns:
        List of normalized event dictionaries.
    """
    if not EVTX_AVAILABLE:
        raise ImportError("python-evtx not installed. Run: pip install python-evtx")

    events = []
    with evtx.Evtx(file_path) as log:
        for record in log.records():
            try:
                xml_str = record.xml()
                event = _parse_evtx_xml(xml_str)
                events.append(event)
            except Exception:
                continue
    return events


def _parse_evtx_xml(xml_str: str) -> Dict[str, Any]:
    """Parse a single EVTX XML record."""
    ns = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
    root = ET.fromstring(xml_str)

    sys = root.find("e:System", ns)
    event_data = root.find("e:EventData", ns)

    timestamp_str = sys.findtext("e:TimeCreated", namespaces=ns)
    if timestamp_str:
        attrib = sys.find("e:TimeCreated", ns)
        timestamp_str = attrib.get("SystemTime", "") if attrib is not None else ""

    data = {}
    if event_data is not None:
        for d in event_data.findall("e:Data", ns):
            name = d.get("Name", "Unknown")
            data[name] = d.text or ""

    return {
        "timestamp": timestamp_str,
        "source": sys.findtext("e:Channel", namespaces=ns) or "Windows",
        "event_id": sys.findtext("e:EventID", namespaces=ns),
        "event_type": _map_event_id(sys.findtext("e:EventID", namespaces=ns)),
        "host": sys.findtext("e:Computer", namespaces=ns),
        "user": data.get("SubjectUserName") or data.get("TargetUserName", ""),
        "ip_address": data.get("IpAddress", ""),
        "process": data.get("NewProcessName") or data.get("ProcessName", ""),
        "severity": _map_severity(sys.findtext("e:Level", namespaces=ns)),
        "description": _build_description(sys.findtext("e:EventID", namespaces=ns), data),
        "raw_data": data,
    }


def _map_event_id(event_id: str) -> str:
    """Map Windows Event IDs to human-readable types."""
    mapping = {
        "4624": "Successful Logon",
        "4625": "Failed Logon",
        "4634": "Logoff",
        "4648": "Logon with Explicit Credentials",
        "4672": "Special Privileges Assigned",
        "4688": "Process Created",
        "4689": "Process Exited",
        "4698": "Scheduled Task Created",
        "4720": "User Account Created",
        "4726": "User Account Deleted",
        "4732": "Member Added to Group",
        "4740": "Account Locked Out",
        "4756": "Member Added to Security Group",
        "4776": "Credential Validation",
        "7045": "Service Installed",
        "1102": "Audit Log Cleared",
        "4663": "File Access Attempt",
        "4656": "Object Handle Requested",
        "4768": "Kerberos TGT Requested",
        "4769": "Kerberos Service Ticket Requested",
    }
    return mapping.get(str(event_id), f"Event ID {event_id}")


def _map_severity(level: str) -> str:
    mapping = {"1": "critical", "2": "high", "3": "medium", "4": "low", "5": "low"}
    return mapping.get(str(level), "low")


def _build_description(event_id: str, data: dict) -> str:
    event_type = _map_event_id(event_id)
    user = data.get("SubjectUserName") or data.get("TargetUserName", "Unknown")
    host = data.get("WorkstationName") or data.get("IpAddress", "")
    return f"{event_type} — User: {user}" + (f" from {host}" if host else "")
