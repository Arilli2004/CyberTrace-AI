"""
CSP Service — High-Level CSP Backtracking Validation Service Orchestrator
"""
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.csp_repository import CSPRepository
from app.reasoning.csp.csp_solver import CSPSolver
from app.models import Evidence, ProcessingStage, GraphValidation


class CSPService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)
        self.graph_repo = GraphRepository(db)
        self.csp_repo = CSPRepository(db)

    async def validate_case_graph(self, case_id: int, user_id: int) -> Dict[str, Any]:
        """Execute CSP Engine with Backtracking over Case Knowledge Graph."""
        nodes, edges = await self.graph_repo.get_full_graph(case_id)
        if not nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Case #{case_id} Knowledge Graph is empty. Please construct Knowledge Graph first.",
            )

        rules = await self.csp_repo.ensure_default_rules()
        rule_map = {r.rule_name: r.id for r in rules}

        # Solve CSP in thread pool
        solver_res = await asyncio.to_thread(CSPSolver.solve_graph_constraints, nodes, edges)

        # Build GraphValidation ORM objects
        validations: List[GraphValidation] = []
        for v in solver_res["violations"]:
            validations.append(
                GraphValidation(
                    uuid_id=str(uuid.uuid4()),
                    case_id=case_id,
                    rule_id=rule_map.get(v["rule_name"]),
                    node_id=v["node_id"],
                    status="VIOLATION",
                    violation_reason=v["reason"],
                    resolution_details=v["suggestion"],
                    confidence=solver_res["confidence_score"],
                )
            )

        for r in solver_res["resolved"]:
            validations.append(
                GraphValidation(
                    uuid_id=str(uuid.uuid4()),
                    case_id=case_id,
                    rule_id=rule_map.get(r["rule_name"]),
                    node_id=r["node_id"],
                    status="RESOLVED",
                    violation_reason=r["reason"],
                    resolution_details=r["resolution"],
                    confidence=0.9,
                )
            )

        # Save Result Record
        res_obj = await self.csp_repo.save_validation_results(
            case_id=case_id,
            status_str=solver_res["validation_status"],
            score=solver_res["validation_score"],
            violations_count=solver_res["violations_count"],
            resolved_count=solver_res["resolved_count"],
            confidence=solver_res["confidence_score"],
            validations=validations,
        )

        # Update Evidence Processing Stage
        evidence_list, _ = await self.evidence_repo.list_evidence(case_id=case_id, limit=100)
        for e in evidence_list:
            if e.graph_status == "completed":
                e.csp_status = "completed"
                e.processing_stage = ProcessingStage.CSP_VALIDATED
                # Log Chain of Custody Audit
                await self.evidence_repo.log_custody_action(
                    evidence_id=e.id,
                    user_id=user_id,
                    action="CSP_VALIDATE",
                    details={
                        "validation_score": solver_res["validation_score"],
                        "violations_count": solver_res["violations_count"],
                        "processing_stage": "CSP_VALIDATED",
                    },
                )
        await self.db.flush()

        return {
            "case_id": case_id,
            "validation_status": solver_res["validation_status"],
            "validation_score": solver_res["validation_score"],
            "violations_count": solver_res["violations_count"],
            "resolved_count": solver_res["resolved_count"],
            "confidence_score": solver_res["confidence_score"],
            "processing_stage": "CSP_VALIDATED",
        }

    async def get_validation_status(self, case_id: int) -> Dict[str, Any]:
        """Query current CSP validation status and latest score."""
        res = await self.csp_repo.get_latest_result(case_id)
        if not res:
            return {
                "case_id": case_id,
                "validation_status": "UNVALIDATED",
                "validation_score": 0.0,
                "violations_count": 0,
                "resolved_count": 0,
                "confidence_score": 0.0,
            }
        return {
            "case_id": case_id,
            "validation_status": res.validation_status,
            "validation_score": res.validation_score,
            "violations_count": res.violations_count,
            "resolved_count": res.resolved_count,
            "confidence_score": res.confidence_score,
        }

    async def get_validation_results(self, case_id: int) -> Dict[str, Any]:
        """Retrieve latest CSP validation run details."""
        res = await self.csp_repo.get_latest_result(case_id)
        violations = await self.csp_repo.list_violations(case_id)

        return {
            "case_id": case_id,
            "result": {
                "case_id": case_id,
                "validation_status": res.validation_status if res else "UNVALIDATED",
                "validation_score": res.validation_score if res else 0.0,
                "violations_count": res.violations_count if res else 0,
                "resolved_count": res.resolved_count if res else 0,
                "confidence_score": res.confidence_score if res else 0.0,
            },
            "violations": [
                {
                    "id": v.id,
                    "status": v.status,
                    "violation_reason": v.violation_reason,
                    "resolution_details": v.resolution_details,
                    "confidence": v.confidence,
                }
                for v in violations
            ],
        }
