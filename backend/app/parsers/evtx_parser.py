"""
Windows EVTX & XML Event Log Parser — CyberTrace AI
"""
import re
from typing import List, Dict, Any
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from app.parsers.base_parser import BaseParser


class EvtxParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        events = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()

            if not content:
                return events

            # Handle XML-formatted EVTX dumps or XML log records
            xml_records = re.findall(r"<Event.*?>.*?</Event>", content, re.DOTALL)
            if not xml_records:
                # If raw binary or fallback text, line-by-line parse
                for line in content.splitlines():
                    if line.strip():
                        events.append(
                            self.create_event_dict(
                                source="WindowsEVTX",
                                event_type="WindowsLog",
                                description=line[:500],
                                raw_event={"raw_line": line},
                            )
                        )
                return events

            for xml_str in xml_records:
                try:
                    root = ET.fromstring(xml_str)
                    ns = {"ns": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}

                    # Extract System Header Fields
                    system_node = root.find("ns:System", ns) if ns else root.find("System")
                    event_id = None
                    source = "Security"
                    computer = "LOCAL_HOST"
                    timestamp = datetime.now(timezone.utc)
                    severity = "low"

                    if system_node is not None:
                        event_id_elem = system_node.find("ns:EventID", ns) if ns else system_node.find("EventID")
                        if event_id_elem is not None and event_id_elem.text:
                            event_id = event_id_elem.text.strip()

                        provider_elem = system_node.find("ns:Provider", ns) if ns else system_node.find("Provider")
                        if provider_elem is not None:
                            source = provider_elem.attrib.get("Name", "WindowsEventLog")

                        comp_elem = system_node.find("ns:Computer", ns) if ns else system_node.find("Computer")
                        if comp_elem is not None and comp_elem.text:
                            computer = comp_elem.text.strip()

                        time_elem = system_node.find("ns:TimeCreated", ns) if ns else system_node.find("TimeCreated")
                        if time_elem is not None:
                            system_time = time_elem.attrib.get("SystemTime")
                            if system_time:
                                try:
                                    timestamp = datetime.fromisoformat(system_time.replace("Z", "+00:00"))
                                except Exception:
                                    pass

                    # Severity mapping based on Windows Event IDs
                    critical_ids = {"1102", "4625", "4688", "7045", "4720", "4726"}
                    high_ids = {"4624", "4672", "4738", "4697"}
                    if event_id in critical_ids:
                        severity = "critical"
                    elif event_id in high_ids:
                        severity = "high"

                    # Extract Data DataFields
                    event_data = {}
                    data_nodes = root.findall(".//ns:Data", ns) if ns else root.findall(".//Data")
                    username = None
                    ip_address = None
                    process_name = None

                    for d in data_nodes:
                        name = d.attrib.get("Name")
                        val = d.text or ""
                        if name:
                            event_data[name] = val
                            if name.lower() in ("targetusername", "subjectusername", "username"):
                                username = val
                            elif name.lower() in ("ipaddress", "workstationname", "sourceaddress"):
                                ip_address = val
                            elif name.lower() in ("newprocessname", "processname", "image"):
                                process_name = val

                    events.append(
                        self.create_event_dict(
                            timestamp=timestamp,
                            hostname=computer,
                            username=username or "SYSTEM",
                            event_type=f"WinEvent_{event_id}" if event_id else "WindowsEvent",
                            event_id=event_id,
                            severity=severity,
                            source=source,
                            ip_address=ip_address,
                            process_name=process_name,
                            description=f"Windows Event Log ID {event_id} on {computer}",
                            raw_event={"xml": xml_str[:1000], "data": event_data},
                        )
                    )
                except Exception:
                    continue

        except Exception as e:
            print(f"EVTX Parse Error on {file_path}: {e}")

        return events
