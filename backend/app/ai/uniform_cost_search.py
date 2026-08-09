"""
Uniform Cost Search (UCS) Engine
Module 8 — Digital Forensics Optimal Attack Path Reconstruction

This module implements Uniform Cost Search (Dijkstra's variant) over the Knowledge Graph.
It uses Python's `heapq` priority queue to evaluate nodes based on minimum cumulative path cost,
reconstructing the most probable sequence of evidence events between a start event and a goal event.
"""
import heapq
import time
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field


@dataclass
class UCSResult:
    """
    Dataclass holding the result of a Uniform Cost Search execution.
    """
    path: List[str]
    total_cost: float
    visited_nodes_count: int
    execution_time_ms: float
    is_path_found: bool
    explanation: str


class UniformCostSearch:
    """
    Uniform Cost Search (UCS) Engine for Knowledge Graph pathfinding.
    
    Time Complexity: O((E + V) * log V) where V is the number of nodes and E is the number of edges.
    Space Complexity: O(V + E) for storing adjacency list, priority queue, and visited set.
    """

    def __init__(self, adjacency_list: Dict[str, List[Tuple[str, float]]]):
        """
        Initialize UCS engine with an adjacency list representation of the graph.
        
        Args:
            adjacency_list: Dict mapping source_node -> List of (destination_node, edge_weight)
        """
        self.adjacency_list = adjacency_list

    def search(self, start_node: str, goal_node: str) -> UCSResult:
        """
        Executes Uniform Cost Search from start_node to goal_node.

        Args:
            start_node: Label or ID of the starting evidence node.
            goal_node: Label or ID of the target evidence node.

        Returns:
            UCSResult containing path, total cost, visited node count, and execution timing.
        """
        start_time = time.perf_counter()

        # Handle trivial case where start equals goal
        if start_node == goal_node:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return UCSResult(
                path=[start_node],
                total_cost=0.0,
                visited_nodes_count=1,
                execution_time_ms=round(elapsed_ms, 3),
                is_path_found=True,
                explanation=f"Start node '{start_node}' is identical to goal node."
            )

        # Priority Queue stores tuples: (cumulative_cost, sequence_counter, current_node, path_so_far)
        # Sequence counter prevents comparison errors when costs are equal
        counter = 0
        priority_queue: List[Tuple[float, int, str, List[str]]] = []
        heapq.heappush(priority_queue, (0.0, counter, start_node, [start_node]))

        visited: Set[str] = set()
        min_cost_to_node: Dict[str, float] = {start_node: 0.0}

        while priority_queue:
            cost, _, current_node, path = heapq.heappop(priority_queue)

            if current_node in visited:
                continue

            visited.add(current_node)

            # Goal Test when popping node from priority queue (guarantees optimal minimum cost)
            if current_node == goal_node:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return UCSResult(
                    path=path,
                    total_cost=round(cost, 4),
                    visited_nodes_count=len(visited),
                    execution_time_ms=round(elapsed_ms, 3),
                    is_path_found=True,
                    explanation=f"Optimal path found with total cost {cost} across {len(visited)} visited nodes."
                )

            # Expand neighbors
            neighbors = self.adjacency_list.get(current_node, [])
            for next_node, edge_weight in neighbors:
                if next_node in visited:
                    continue

                new_cost = cost + max(0.01, edge_weight)  # Ensure non-negative edge costs

                if next_node not in min_cost_to_node or new_cost < min_cost_to_node[next_node]:
                    min_cost_to_node[next_node] = new_cost
                    counter += 1
                    heapq.heappush(
                        priority_queue,
                        (new_cost, counter, next_node, path + [next_node])
                    )

        # Path not found
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return UCSResult(
            path=[],
            total_cost=float("inf"),
            visited_nodes_count=len(visited),
            execution_time_ms=round(elapsed_ms, 3),
            is_path_found=False,
            explanation=f"No path exists between start_node '{start_node}' and goal_node '{goal_node}'."
        )
