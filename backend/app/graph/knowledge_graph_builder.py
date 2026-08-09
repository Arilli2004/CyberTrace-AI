"""
Knowledge Graph Builder — High-Level Knowledge Graph Construction Pipeline
"""
import uuid
from typing import List, Dict, Any, Tuple
from app.models import NormalizedEvent, GraphNode, GraphEdge, GraphMetadata
from app.graph.entity_extractor import EntityExtractor
from app.graph.relationship_extractor import RelationshipExtractor
from app.graph.node_deduplicator import NodeDeduplicator
from app.graph.weight_calculator import WeightCalculator


class KnowledgeGraphBuilder:
    @classmethod
    def build_graph(cls, norm_events: List[NormalizedEvent], case_id: int) -> Tuple[List[GraphNode], List[GraphEdge], GraphMetadata]:
        """
        Construct a complete Knowledge Graph (nodes, weighted edges, and metadata) from normalized events.
        """
        deduplicator = NodeDeduplicator()
        edge_objects: List[GraphEdge] = []

        for evt in norm_events:
            # 1. Extract and Deduplicate Entity Nodes
            node_descriptors = EntityExtractor.extract_nodes(evt)
            for ntype, nlabel, nprops in node_descriptors:
                deduplicator.get_or_register(node_type=ntype, node_label=nlabel, properties=nprops, case_id=case_id)

            # 2. Extract Relationships and Construct Edges
            raw_edges = RelationshipExtractor.extract_edges(evt)
            for redge in raw_edges:
                src_type, src_label = redge["source"]
                dst_type, dst_label = redge["destination"]

                src_node, _ = deduplicator.get_or_register(node_type=src_type, node_label=src_label, properties={}, case_id=case_id)
                dst_node, _ = deduplicator.get_or_register(node_type=dst_type, node_label=dst_label, properties={}, case_id=case_id)

                calc_weight = WeightCalculator.calculate_weight(
                    severity=evt.severity,
                    confidence=redge.get("confidence", 0.8)
                )

                edge_objects.append(
                    GraphEdge(
                        uuid_id=str(uuid.uuid4()),
                        case_id=case_id,
                        source_node=src_node,
                        destination_node=dst_node,
                        edge_type=redge["edge_type"].value if hasattr(redge["edge_type"], "value") else str(redge["edge_type"]),
                        weight=calc_weight,
                        confidence=redge.get("confidence", 0.8),
                        timestamp=redge.get("timestamp"),
                        properties=redge.get("properties", {}),
                    )
                )

        nodes = deduplicator.get_all_nodes()
        node_count = len(nodes)
        edge_count = len(edge_objects)
        density = round(edge_count / max(1, node_count * (node_count - 1)), 4) if node_count > 1 else 0.0

        metadata = GraphMetadata(
            case_id=case_id,
            node_count=node_count,
            edge_count=edge_count,
            connected_components=1 if node_count > 0 else 0,
            density=density,
        )

        return nodes, edge_objects, metadata
