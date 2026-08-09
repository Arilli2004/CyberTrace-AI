"""
CSP Solver — High-Level Constraint Satisfaction Problem Solver Entrypoint
"""
from typing import List, Dict, Any
from app.models import GraphNode, GraphEdge
from app.reasoning.csp.backtracking_engine import BacktrackingEngine


class CSPSolver:
    @classmethod
    def solve_graph_constraints(cls, nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, Any]:
        """
        Formulate Knowledge Graph into CSP variables/constraints and solve with Backtracking Engine.
        """
        engine = BacktrackingEngine()
        return engine.solve(nodes, edges)
