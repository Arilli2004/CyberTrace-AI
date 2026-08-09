"""
Forward Chaining Service Layer — CyberTrace AI
Module 10 — Data-Driven Forensic Threat Reasoning

Coordinates Case validation, Knowledge Base fact extraction from Normalized Events & Database,
Forward Chaining Engine execution, logging, and response formatting.
"""
import logging
from typing import Dict, List, Set, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Case, Event, NormalizedEvent, GraphNode, GraphEdge
from app.ai.forward_chaining import ForwardChainingEngine, Fact, ForwardChainingResult, get_standard_forensic_rules
from app.schemas.forward_chaining import ForwardChainingRequest, ForwardChainingResponse, FiredRuleSchema

logger = logging.getLogger(__name__)


class ForwardChainingService:
    """
    Service class providing high-level Forward Chaining threat reasoning over PostgreSQL case evidence.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = ForwardChainingEngine(rules=get_standard_forensic_rules())

    async def run_forward_chaining(self, request: ForwardChainingRequest) -> ForwardChainingResponse:
        """
        Extracts facts from Case evidence in database, merges optional custom facts,
        and runs forward chaining rule-based inference.

        Args:
            request: ForwardChainingRequest schema containing case_id and optional custom_facts.

        Returns:
            ForwardChainingResponse containing derived threat facts and fired rules.

        Raises:
            HTTPException 404: Case not found.
        """
        # 1. Validate Case Existence
        case_stmt = select(Case).where(Case.id == request.case_id, Case.is_deleted == False)
        case_res = await self.db.execute(case_stmt)
        case = case_res.scalar_one_or_none()
        if not case:
            logger.warning("Forward Chaining failed: Case ID %s not found.", request.case_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {request.case_id} not found."
            )

        # 2. Extract Initial Facts from Database (Normalized Events & Raw Events)
        initial_facts: List[Fact] = []
        fact_counter = 1

        # Query Normalized Events for Case
        norm_stmt = select(NormalizedEvent).where(NormalizedEvent.case_id == request.case_id)
        norm_res = await self.db.execute(norm_stmt)
        norm_events: List[NormalizedEvent] = list(norm_res.scalars().all())

        auth_fail_count = 0
        for ne in norm_events:
            action_upper = (ne.action or "").upper()
            cmd_upper = (ne.command_line or "").upper()
            proc_upper = (ne.process_name or "").upper()

            if "FAIL" in action_upper or "DENIED" in action_upper:
                auth_fail_count += 1
                initial_facts.append(Fact(
                    fact_id=f"DB_F_{fact_counter}",
                    fact_type="AUTH_FAILURE",
                    entity=f"user:{ne.username or 'unknown'}",
                    value=ne.action,
                    confidence=0.9
                ))
                fact_counter += 1

            if "VSSADMIN" in cmd_upper or "DELETE SHADOWS" in cmd_upper:
                initial_facts.append(Fact(
                    fact_id=f"DB_F_{fact_counter}",
                    fact_type="SHADOW_COPY_DELETION",
                    entity=f"host:{ne.hostname or 'unknown'}",
                    value=ne.command_line,
                    confidence=0.95
                ))
                fact_counter += 1

            if "POWERSHELL" in proc_upper or "CMD.EXE" in proc_upper:
                initial_facts.append(Fact(
                    fact_id=f"DB_F_{fact_counter}",
                    fact_type="SUSPICIOUS_PROCESS_EXECUTION",
                    entity=f"host:{ne.hostname or 'unknown'}",
                    value=ne.process_name,
                    confidence=0.85
                ))
                fact_counter += 1

            if "WMI" in proc_upper or "WMIPRVSE" in proc_upper or "WMI" in cmd_upper:
                initial_facts.append(Fact(
                    fact_id=f"DB_F_{fact_counter}",
                    fact_type="WMI_EXECUTION",
                    entity=f"host:{ne.hostname or 'unknown'}",
                    value=ne.command_line or ne.process_name,
                    confidence=0.9
                ))
                fact_counter += 1

        if auth_fail_count >= 3:
            initial_facts.append(Fact(
                fact_id=f"DB_F_{fact_counter}",
                fact_type="AUTH_FAILURE_BURST",
                entity="AUTHENTICATION_SERVICE",
                value=f"{auth_fail_count}_failures",
                confidence=0.9
            ))
            fact_counter += 1

        # 3. Merge Optional Custom Payload Facts
        if request.custom_facts:
            for cf in request.custom_facts:
                initial_facts.append(Fact(
                    fact_id=cf.fact_id or f"CUSTOM_F_{fact_counter}",
                    fact_type=cf.fact_type,
                    entity=cf.entity,
                    value=cf.value,
                    confidence=cf.confidence,
                    properties=cf.properties or {}
                ))
                fact_counter += 1

        # 4. Execute Forward Chaining Inference Engine
        logger.info("Running Forward Chaining for Case ID %d with %d initial fact(s).", request.case_id, len(initial_facts))
        result: ForwardChainingResult = self.engine.run_inference(initial_facts)

        # 5. Format Fired Rules for Response
        fired_rules_formatted = [
            FiredRuleSchema(
                rule_id=fr.rule_id,
                rule_name=fr.rule_name,
                category=fr.category,
                severity=fr.severity,
                triggering_facts=fr.triggering_facts,
                derived_facts=fr.derived_facts
            )
            for fr in result.fired_rules
        ]

        logger.info(
            "Forward Chaining completed for Case ID %d | Fired Rules: %d | Derived Facts: %d | Time: %.3f ms",
            request.case_id, len(result.fired_rules), len(result.derived_facts), result.execution_time_ms
        )

        return ForwardChainingResponse(
            success=True,
            case_id=request.case_id,
            initial_facts_count=result.initial_facts_count,
            total_facts_count=result.total_facts_count,
            derived_facts=result.derived_facts,
            fired_rules=fired_rules_formatted,
            iterations=result.iterations,
            execution_time_ms=result.execution_time_ms,
            explanation=result.explanation
        )
