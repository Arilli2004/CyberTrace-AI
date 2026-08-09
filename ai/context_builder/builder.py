"""
AI Context Builder — CyberTrace AI
Constructs prompt contexts for LLM investigation analysis.
"""
from typing import List, Dict, Any


def build_investigation_prompt(case_title: str, events: List[Dict[str, Any]], alerts: List[Dict[str, Any]]) -> str:
    """Build structured context prompt for AI analysis."""
    lines = [f"=== CASE INVESTIGATION: {case_title} ===", "\n--- ALERTS ---"]
    for a in alerts:
        lines.append(f"[{a.get('severity', 'HIGH').upper()}] {a.get('title')} — Rule: {a.get('rule_name')}")

    lines.append("\n--- CHRONOLOGICAL TIMELINE ---")
    for e in events[:150]:
        lines.append(
            f"[{e.get('timestamp')}] {e.get('event_type')} | User: {e.get('user', 'N/A')} | Host: {e.get('host', 'N/A')} | IP: {e.get('ip_address', 'N/A')} | {e.get('description')}"
        )

    return "\n".join(lines)
