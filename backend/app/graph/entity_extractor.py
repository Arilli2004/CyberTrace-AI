"""
Entity Extractor — Extracts Graph Node Descriptors from Normalized Events
"""
from typing import List, Dict, Any, Tuple
from app.models import NormalizedEvent
from app.graph.graph_taxonomy import NodeType


class EntityExtractor:
    @classmethod
    def extract_nodes(cls, norm_event: NormalizedEvent) -> List[Tuple[NodeType, str, Dict[str, Any]]]:
        """
        Extract list of node tuples (node_type, node_label, properties) from a NormalizedEvent.
        """
        nodes = []

        # 1. Host Node
        if norm_event.hostname:
            nodes.append((
                NodeType.HOST,
                norm_event.hostname,
                {"device_name": norm_event.device_name, "case_id": norm_event.case_id}
            ))

        # 2. User / Account Node
        if norm_event.username:
            user_label = f"{norm_event.domain}\\{norm_event.username}" if norm_event.domain else norm_event.username
            nodes.append((
                NodeType.USER,
                user_label,
                {"username": norm_event.username, "domain": norm_event.domain}
            ))

        # 3. IP Address Node
        if norm_event.ip_address:
            nodes.append((
                NodeType.IP_ADDRESS,
                norm_event.ip_address,
                {"type": "source_ip"}
            ))
        if norm_event.destination_ip:
            nodes.append((
                NodeType.IP_ADDRESS,
                norm_event.destination_ip,
                {"type": "destination_ip", "port": norm_event.destination_port}
            ))

        # 4. Process & Parent Process Nodes
        if norm_event.process_name:
            nodes.append((
                NodeType.PROCESS,
                norm_event.process_name,
                {
                    "process_id": norm_event.process_id,
                    "command_line": norm_event.command_line,
                }
            ))
        if norm_event.parent_process:
            nodes.append((
                NodeType.PARENT_PROCESS,
                norm_event.parent_process,
                {}
            ))

        # 5. File Node
        if norm_event.file_path:
            nodes.append((
                NodeType.FILE,
                norm_event.file_path,
                {"object_name": norm_event.object_name}
            ))

        # 6. Registry Key Node
        if norm_event.registry_key:
            nodes.append((
                NodeType.REGISTRY_KEY,
                norm_event.registry_key,
                {}
            ))

        # 7. Evidence & Event Nodes
        nodes.append((
            NodeType.EVIDENCE,
            f"Evidence_{norm_event.evidence_id}",
            {"evidence_id": norm_event.evidence_id}
        ))
        nodes.append((
            NodeType.NORMALIZED_EVENT,
            f"Event_{norm_event.uuid_id[:8]}",
            {
                "event_uuid": norm_event.uuid_id,
                "action": norm_event.action,
                "category": norm_event.event_category.value,
                "severity": norm_event.severity.value,
                "timestamp": norm_event.timestamp_utc.isoformat() if norm_event.timestamp_utc else None,
            }
        ))

        return nodes
