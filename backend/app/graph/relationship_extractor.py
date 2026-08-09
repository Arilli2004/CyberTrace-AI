"""
Relationship Extractor — Extracts Behavioral Relationships and Edges from Normalized Events
"""
from typing import List, Dict, Any, Tuple
from app.models import NormalizedEvent, EventCategory
from app.graph.graph_taxonomy import NodeType, EdgeType


class RelationshipExtractor:
    @classmethod
    def extract_edges(cls, norm_event: NormalizedEvent) -> List[Dict[str, Any]]:
        """
        Extract directed relationships between entities from a NormalizedEvent.
        Each edge returns a dictionary containing source, destination, edge_type, timestamp, and properties.
        """
        edges = []

        host_label = norm_event.hostname or "UNKNOWN_HOST"
        user_label = f"{norm_event.domain}\\{norm_event.username}" if norm_event.domain else (norm_event.username or "UNKNOWN_USER")
        event_label = f"Event_{norm_event.uuid_id[:8]}"
        evidence_label = f"Evidence_{norm_event.evidence_id}"

        # 1. User -> Host Authentication Edges
        if norm_event.event_category == EventCategory.AUTHENTICATION:
            if norm_event.action == "AUTH_SUCCESS":
                edges.append({
                    "source": (NodeType.USER, user_label),
                    "destination": (NodeType.HOST, host_label),
                    "edge_type": EdgeType.AUTHENTICATED,
                    "timestamp": norm_event.timestamp_utc,
                    "confidence": norm_event.confidence_score,
                    "properties": {"action": norm_event.action, "ip": norm_event.ip_address},
                })
            elif norm_event.action == "AUTH_FAILURE":
                edges.append({
                    "source": (NodeType.USER, user_label),
                    "destination": (NodeType.HOST, host_label),
                    "edge_type": EdgeType.FAILED_AUTH,
                    "timestamp": norm_event.timestamp_utc,
                    "confidence": norm_event.confidence_score,
                    "properties": {"action": norm_event.action, "ip": norm_event.ip_address},
                })

        # 2. Process Execution Edges
        if norm_event.process_name:
            # User EXECUTED Process
            edges.append({
                "source": (NodeType.USER, user_label),
                "destination": (NodeType.PROCESS, norm_event.process_name),
                "edge_type": EdgeType.EXECUTED,
                "timestamp": norm_event.timestamp_utc,
                "confidence": norm_event.confidence_score,
                "properties": {"pid": norm_event.process_id, "cmd": norm_event.command_line},
            })

            # Parent Process SPAWNED Child Process
            if norm_event.parent_process:
                edges.append({
                    "source": (NodeType.PARENT_PROCESS, norm_event.parent_process),
                    "destination": (NodeType.PROCESS, norm_event.process_name),
                    "edge_type": EdgeType.SPAWNED,
                    "timestamp": norm_event.timestamp_utc,
                    "confidence": norm_event.confidence_score,
                    "properties": {"parent": norm_event.parent_process},
                })

        # 3. File Activity Edges
        if norm_event.file_path:
            process_or_user = (NodeType.PROCESS, norm_event.process_name) if norm_event.process_name else (NodeType.USER, user_label)
            action_edge = EdgeType.MODIFIED
            if "write" in norm_event.action.lower() or "create" in norm_event.action.lower():
                action_edge = EdgeType.WROTE
            elif "read" in norm_event.action.lower() or "access" in norm_event.action.lower():
                action_edge = EdgeType.READ
            elif "delete" in norm_event.action.lower():
                action_edge = EdgeType.DELETED

            edges.append({
                "source": process_or_user,
                "destination": (NodeType.FILE, norm_event.file_path),
                "edge_type": action_edge,
                "timestamp": norm_event.timestamp_utc,
                "confidence": norm_event.confidence_score,
                "properties": {"file": norm_event.file_path},
            })

        # 4. Network Connection Edges
        if norm_event.ip_address and norm_event.destination_ip:
            edges.append({
                "source": (NodeType.IP_ADDRESS, norm_event.ip_address),
                "destination": (NodeType.IP_ADDRESS, norm_event.destination_ip),
                "edge_type": EdgeType.COMMUNICATED_WITH,
                "timestamp": norm_event.timestamp_utc,
                "confidence": norm_event.confidence_score,
                "properties": {"port": norm_event.destination_port, "protocol": norm_event.network_protocol},
            })

        # 5. Registry Persistence Edges
        if norm_event.registry_key:
            edges.append({
                "source": (NodeType.PROCESS, norm_event.process_name) if norm_event.process_name else (NodeType.USER, user_label),
                "destination": (NodeType.REGISTRY_KEY, norm_event.registry_key),
                "edge_type": EdgeType.PERSISTED,
                "timestamp": norm_event.timestamp_utc,
                "confidence": norm_event.confidence_score,
                "properties": {"key": norm_event.registry_key},
            })

        # 6. Event & Evidence Provenance Edges
        edges.append({
            "source": (NodeType.NORMALIZED_EVENT, event_label),
            "destination": (NodeType.EVIDENCE, evidence_label),
            "edge_type": EdgeType.BELONGS_TO,
            "timestamp": norm_event.timestamp_utc,
            "confidence": 1.0,
            "properties": {"event_uuid": norm_event.uuid_id},
        })

        return edges
