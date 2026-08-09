"""
Weight Calculator — Computes Traversal Costs & Weights for Uniform Cost Search (UCS) & A* Search
"""
from typing import Dict, Any
from app.models import SeverityLevel


class WeightCalculator:
    # Severity cost multipliers for traversal heuristic (higher multiplier = lower edge weight = shortest path attractor)
    SEVERITY_MULTIPLIER: Dict[SeverityLevel, float] = {
        SeverityLevel.critical: 5.0,
        SeverityLevel.high: 2.0,
        SeverityLevel.medium: 1.2,
        SeverityLevel.low: 1.0,
    }

    @classmethod
    def calculate_weight(cls, severity: SeverityLevel, confidence: float = 0.8) -> float:
        """
        Calculate traversal cost weight for an edge.
        Formula: weight = 1.0 / (confidence * severity_multiplier)
        Critical threat edges have smaller weights, attracting graph search algorithms.
        """
        mult = cls.SEVERITY_MULTIPLIER.get(severity, 1.0)
        conf = max(0.1, min(1.0, confidence or 0.8))
        weight = round(1.0 / (conf * mult), 3)
        return weight
