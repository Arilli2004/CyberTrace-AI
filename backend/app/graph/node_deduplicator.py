"""
Node Deduplicator — Ensures Unique Graph Nodes per Investigation Case
"""
from typing import Dict, Tuple, Any
from app.graph.graph_taxonomy import NodeType


class NodeDeduplicator:
    """
    In-memory registry preventing duplicate node creation for the same forensic entity within a case.
    Key: (NodeType, node_label)
    Value: GraphNode ORM instance / temporary ID
    """
    def __init__(self):
        self._nodes_map: Dict[Tuple[str, str], Any] = {}

    def get_or_register(self, node_type: NodeType, node_label: str, properties: Dict[str, Any], case_id: int) -> Tuple[Any, bool]:
        """
        Get existing node or register a new node. Returns (node_object, is_new_boolean).
        """
        key = (node_type.value if hasattr(node_type, "value") else str(node_type), str(node_label).strip())

        if key in self._nodes_map:
            # Existing node
            existing_node = self._nodes_map[key]
            # Merge additional properties
            if properties and hasattr(existing_node, "properties") and isinstance(existing_node.properties, dict):
                existing_node.properties.update(properties)
            return existing_node, False
        else:
            from app.models import GraphNode
            import uuid
            new_node = GraphNode(
                uuid_id=str(uuid.uuid4()),
                case_id=case_id,
                node_type=key[0],
                node_label=key[1],
                properties=properties or {},
            )
            self._nodes_map[key] = new_node
            return new_node, True

    def get_all_nodes(self):
        return list(self._nodes_map.values())

    def clear(self):
        self._nodes_map.clear()
