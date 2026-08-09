"""
A* Search Engine Module
Module 9 — Digital Forensics Optimal Attack Path Reconstruction

This module implements the A* Search algorithm over Knowledge Graphs.
It combines cumulative path cost g(n) with an admissible heuristic function h(n)
to evaluate f(n) = g(n) + h(n), guiding search towards the goal node and
significantly reducing the number of explored graph nodes compared to UCS.
"""
import heapq
import time
from typing import Dict, List, Set, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class AStarResult:
    """
    Dataclass holding execution results and performance metrics of A* Search.
    """
    path: List[str]
    total_cost: float
    heuristic_cost: float
    visited_nodes_count: int
    execution_time_ms: float
    is_path_found: bool
    explanation: str


class BaseHeuristic(ABC):
    """
    Abstract base class for pluggable A* heuristic functions.
    Custom heuristics must inherit from this class and implement `evaluate`.
    """

    @abstractmethod
    def evaluate(self, current_node: str, goal_node: str, node_properties: Dict[str, Any]) -> float:
        """
        Calculates estimated cost h(n) from current_node to goal_node.
        Must be admissible (h(n) <= h*(n)) to guarantee optimal pathfinding.
        """
        pass


class HopDistanceHeuristic(BaseHeuristic):
    """
    Default pluggable heuristic estimating remaining path cost based on graph topological distance
    or node privilege/category gaps.
    """

    def evaluate(self, current_node: str, goal_node: str, node_properties: Dict[str, Any]) -> float:
        if current_node == goal_node:
            return 0.0

        # Extract privilege or criticality properties if available
        curr_props = node_properties.get(current_node, {})
        goal_props = node_properties.get(goal_node, {})

        curr_priv = curr_props.get("privilege_level", 1)
        goal_priv = goal_props.get("privilege_level", 1)

        # Admissible heuristic: privilege gap multiplier (never overestimates)
        priv_gap = max(0, goal_priv - curr_priv)
        return float(priv_gap * 0.5)


class DefaultZeroHeuristic(BaseHeuristic):
    """
    Zero heuristic (h(n) = 0). When used, A* gracefully reduces to Uniform Cost Search (UCS).
    """

    def evaluate(self, current_node: str, goal_node: str, node_properties: Dict[str, Any]) -> float:
        return 0.0


class AStarSearch:
    """
    A* Search Engine for Knowledge Graph pathfinding.

    Evaluation function: f(n) = g(n) + h(n)
    where:
      g(n) = exact path cost from start_node to node n
      h(n) = estimated admissible heuristic cost from node n to goal_node
      f(n) = estimated total cost of cheapest solution through node n

    Time Complexity: O((E + V) * log V) in worst case, significantly faster in practice with good h(n).
    Space Complexity: O(V + E) for open set, closed set, and path tracking dictionaries.
    """

    def __init__(
        self,
        adjacency_list: Dict[str, List[Tuple[str, float]]],
        heuristic: Optional[BaseHeuristic] = None,
        node_properties: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize A* Search Engine.

        Args:
            adjacency_list: Dict mapping source_node -> List of (destination_node, edge_weight)
            heuristic: Pluggable BaseHeuristic instance (defaults to HopDistanceHeuristic)
            node_properties: Optional Dict containing metadata/properties per node for heuristics
        """
        self.adjacency_list = adjacency_list
        self.heuristic = heuristic or HopDistanceHeuristic()
        self.node_properties = node_properties or {}

    def search(self, start_node: str, goal_node: str) -> AStarResult:
        """
        Executes A* Search algorithm from start_node to goal_node.

        Args:
            start_node: Starting evidence node identifier/label.
            goal_node: Destination evidence node identifier/label.

        Returns:
            AStarResult containing path, total cost, initial heuristic cost, visited node count, and timing.
        """
        start_time = time.perf_counter()

        initial_h = self.heuristic.evaluate(start_node, goal_node, self.node_properties)

        # Handle trivial case where start equals goal
        if start_node == goal_node:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AStarResult(
                path=[start_node],
                total_cost=0.0,
                heuristic_cost=0.0,
                visited_nodes_count=1,
                execution_time_ms=round(elapsed_ms, 3),
                is_path_found=True,
                explanation=f"Start node '{start_node}' is identical to goal node."
            )

        # Priority queue (Open Set) stores tuples:
        # (f_score, g_score, sequence_counter, current_node, path_so_far)
        counter = 0
        open_set: List[Tuple[float, float, int, str, List[str]]] = []
        heapq.heappush(open_set, (initial_h, 0.0, counter, start_node, [start_node]))

        closed_set: Set[str] = set()  # Closed Set (Visited nodes)
        g_score: Dict[str, float] = {start_node: 0.0}

        while open_set:
            f, g, _, current_node, path = heapq.heappop(open_set)

            if current_node in closed_set:
                continue

            closed_set.add(current_node)

            # Goal Test when popping from Open Set guarantees optimal path
            if current_node == goal_node:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return AStarResult(
                    path=path,
                    total_cost=round(g, 4),
                    heuristic_cost=round(initial_h, 4),
                    visited_nodes_count=len(closed_set),
                    execution_time_ms=round(elapsed_ms, 3),
                    is_path_found=True,
                    explanation=(
                        f"Optimal path found via A* Search with total cost {round(g, 4)} "
                        f"and initial heuristic {round(initial_h, 4)} across {len(closed_set)} visited nodes."
                    )
                )

            # Expand neighbors
            neighbors = self.adjacency_list.get(current_node, [])
            for next_node, edge_weight in neighbors:
                if next_node in closed_set:
                    continue

                tentative_g = g + max(0.01, edge_weight)

                if next_node not in g_score or tentative_g < g_score[next_node]:
                    g_score[next_node] = tentative_g
                    h_next = self.heuristic.evaluate(next_node, goal_node, self.node_properties)
                    f_next = tentative_g + h_next
                    counter += 1
                    heapq.heappush(
                        open_set,
                        (f_next, tentative_g, counter, next_node, path + [next_node])
                    )

        # Path not found
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return AStarResult(
            path=[],
            total_cost=float("inf"),
            heuristic_cost=round(initial_h, 4),
            visited_nodes_count=len(closed_set),
            execution_time_ms=round(elapsed_ms, 3),
            is_path_found=False,
            explanation=f"No valid path exists between start_node '{start_node}' and goal_node '{goal_node}'."
        )
