"""
Field Mapper — Extract Standardized Attributes (IPs, Ports, Users, Processes, Domains)
"""
import re
from typing import Dict, Any, Optional, Tuple


class FieldMapper:
    IP_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    @classmethod
    def extract_fields(cls, raw_event_dict: Dict[str, Any], description: str) -> Dict[str, Any]:
        """
        Extract missing attributes like IP address, process name, command line, domain, and object name.
        """
        extracted = {}

        # IP Address Extraction
        if not raw_event_dict.get("ip_address") and description:
            ips = cls.IP_REGEX.findall(description)
            if ips:
                extracted["ip_address"] = ips[0]

        # Domain Extraction
        if "domain" not in extracted:
            user_val = raw_event_dict.get("user") or ""
            if "\\" in user_val:
                parts = user_val.split("\\", 1)
                extracted["domain"] = parts[0]
                extracted["username"] = parts[1]
            elif "@" in user_val:
                parts = user_val.split("@", 1)
                extracted["username"] = parts[0]
                extracted["domain"] = parts[1]

        # Command Line & Parent Process
        raw_data = raw_event_dict.get("raw_data") or {}
        if isinstance(raw_data, dict):
            extracted["command_line"] = raw_data.get("CommandLine") or raw_data.get("command_line") or raw_data.get("cmd")
            extracted["parent_process"] = raw_data.get("ParentProcessName") or raw_data.get("parent_process")
            extracted["process_id"] = str(raw_data.get("ProcessId") or raw_data.get("pid") or "")
            extracted["object_name"] = raw_data.get("ObjectName") or raw_data.get("object_name")
            extracted["registry_key"] = raw_data.get("TargetObject") or raw_data.get("registry_key")
            extracted["network_protocol"] = raw_data.get("Protocol") or raw_data.get("network_protocol") or "TCP"
            
            dest_ip = raw_data.get("DestinationIp") or raw_data.get("dest_ip")
            if dest_ip:
                extracted["destination_ip"] = str(dest_ip)
            dest_port = raw_data.get("DestinationPort") or raw_data.get("dest_port")
            if dest_port and str(dest_port).isdigit():
                extracted["destination_port"] = int(dest_port)

        return extracted
