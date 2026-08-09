"""
Constraint Rules — Defines Forensic Graph Consistency Rules
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from app.models import GraphNode, GraphEdge


class BaseConstraintRule(ABC):
    """Abstract Base Class for all Graph Constraint Rules."""
    name: str
    category: str
    description: str

    @abstractmethod
    def evaluate(self, node: GraphNode, edges: List[GraphEdge]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Evaluate constraint rule on node and adjacent edges.
        Returns: (is_valid, violation_reason, suggested_resolution)
        """
        pass


class TemporalOrderRule(BaseConstraintRule):
    name = "Temporal Sequence Consistency"
    category = "Temporal"
    description = "Ensures connected behavioral events maintain chronological timestamp ordering."

    def evaluate(self, node: GraphNode, edges: List[GraphEdge]) -> Tuple[bool, Optional[str], Optional[str]]:
        timestamps = [e.timestamp for e in edges if e.timestamp is not None]
        if len(timestamps) > 1:
            # Check if any edge timestamp is inexplicably in the future compared to node creation
            sorted_ts = sorted(timestamps)
            if (sorted_ts[-1] - sorted_ts[0]).total_seconds() < -1:
                return (
                    False,
                    f"Temporal anomaly detected on node '{node.node_label}': Out of sequence timestamps.",
                    "Re-order event timeline sequence."
                )
        return True, None, None


class ProcessTreeRule(BaseConstraintRule):
    name = "Process Tree Parent-Child Consistency"
    category = "Process"
    description = "Validates that child process creation follows parent process existence."

    def evaluate(self, node: GraphNode, edges: List[GraphEdge]) -> Tuple[bool, Optional[str], Optional[str]]:
        if node.node_type == "Process":
            spawned_edges = [e for e in edges if e.edge_type == "SPAWNED"]
            for edge in spawned_edges:
                if not edge.source_node_id:
                    return (
                        False,
                        f"Orphan process execution on '{node.node_label}': Missing parent process link.",
                        "Bind orphan process to SYSTEM root parent node."
                    )
        return True, None, None


class FileLifecycleRule(BaseConstraintRule):
    name = "File Lifecycle Operations Consistency"
    category = "File"
    description = "Ensures file operations follow valid lifecycle order (CREATED -> MODIFIED -> DELETED)."

    def evaluate(self, node: GraphNode, edges: List[GraphEdge]) -> Tuple[bool, Optional[str], Optional[str]]:
        if node.node_type == "File":
            operations = [e.edge_type for e in edges]
            if "DELETED" in operations and "WROTE" not in operations and "CREATED" not in operations and "READ" not in operations:
                return (
                    False,
                    f"File lifecycle anomaly on '{node.node_label}': File deletion without prior creation or write access.",
                    "Infer missing file write reference."
                )
        return True, None, None


class AuthSessionRule(BaseConstraintRule):
    name = "User Authentication Session Validity"
    category = "Authentication"
    description = "Validates that user process executions and network activity occur within valid authenticated sessions."

    def evaluate(self, node: GraphNode, edges: List[GraphEdge]) -> Tuple[bool, Optional[str], Optional[str]]:
        if node.node_type == "User":
            failed_auths = [e for e in edges if e.edge_type == "FAILED_AUTH"]
            executed = [e for e in edges if e.edge_type == "EXECUTED"]
            if failed_auths and executed:
                # Check if all auth attempts were failures
                authenticated = [e for e in edges if e.edge_type == "AUTHENTICATED"]
                if not authenticated:
                    return (
                        False,
                        f"Authentication violation for '{node.node_label}': Process executions recorded with 0 successful authentications.",
                        "Flag account for credential theft or lateral movement investigation."
                    )
        return True, None, None


class NetworkFlowRule(BaseConstraintRule):
    name = "Network Flow & Protocol Consistency"
    category = "Network"
    description = "Verifies IP address formatting and network communication protocol parameters."

    def evaluate(self, node: GraphNode, edges: List[GraphEdge]) -> Tuple[bool, Optional[str], Optional[str]]:
        if node.node_type == "IP_Address":
            comm_edges = [e for e in edges if e.edge_type == "COMMUNICATED_WITH"]
            for edge in comm_edges:
                props = edge.properties or {}
                port = props.get("port")
                if port and (not isinstance(port, int) or port < 0 or port > 65535):
                    return (
                        False,
                        f"Network port boundary violation on '{node.node_label}': Invalid port {port}.",
                        "Sanitize port value to standard TCP/UDP range."
                    )
        return True, None, None


# Standard Rule Catalog
STANDARD_CSP_RULES: List[BaseConstraintRule] = [
    TemporalOrderRule(),
    ProcessTreeRule(),
    FileLifecycleRule(),
    AuthSessionRule(),
    NetworkFlowRule(),
]
