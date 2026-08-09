"""
CSP Repository — Persistence Access Layer for Constraint Validation Results & Rules
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional, List, Tuple

from app.models import ConstraintRule, ConstraintResult, GraphValidation, SeverityLevel
import uuid


class CSPRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_default_rules(self) -> List[ConstraintRule]:
        """Seed default CSP constraint rules if table is empty."""
        result = await self.db.execute(select(ConstraintRule))
        existing = result.scalars().all()
        if existing:
            return list(existing)

        default_rules = [
            ConstraintRule(
                uuid_id=str(uuid.uuid4()),
                rule_name="Temporal Sequence Consistency",
                category="Temporal",
                description="Ensures connected behavioral events maintain chronological timestamp ordering.",
                severity=SeverityLevel.medium,
            ),
            ConstraintRule(
                uuid_id=str(uuid.uuid4()),
                rule_name="Process Tree Parent-Child Consistency",
                category="Process",
                description="Validates that child process creation follows parent process existence.",
                severity=SeverityLevel.high,
            ),
            ConstraintRule(
                uuid_id=str(uuid.uuid4()),
                rule_name="File Lifecycle Operations Consistency",
                category="File",
                description="Ensures file operations follow valid lifecycle order (CREATED -> MODIFIED -> DELETED).",
                severity=SeverityLevel.medium,
            ),
            ConstraintRule(
                uuid_id=str(uuid.uuid4()),
                rule_name="User Authentication Session Validity",
                category="Authentication",
                description="Validates that user process executions and network activity occur within valid authenticated sessions.",
                severity=SeverityLevel.critical,
            ),
            ConstraintRule(
                uuid_id=str(uuid.uuid4()),
                rule_name="Network Flow & Protocol Consistency",
                category="Network",
                description="Verifies IP address formatting and network communication protocol parameters.",
                severity=SeverityLevel.medium,
            ),
        ]

        self.db.add_all(default_rules)
        await self.db.flush()
        return default_rules

    async def save_validation_results(
        self,
        case_id: int,
        status_str: str,
        score: float,
        violations_count: int,
        resolved_count: int,
        confidence: float,
        validations: List[GraphValidation],
    ) -> ConstraintResult:
        """Save CSP validation run result and detailed violation records."""
        res_obj = ConstraintResult(
            uuid_id=str(uuid.uuid4()),
            case_id=case_id,
            validation_status=status_str,
            validation_score=score,
            violations_count=violations_count,
            resolved_count=resolved_count,
            confidence_score=confidence,
        )
        self.db.add(res_obj)
        await self.db.flush()

        for val in validations:
            val.result_id = res_obj.id
            self.db.add(val)
        await self.db.flush()

        return res_obj

    async def get_latest_result(self, case_id: int) -> Optional[ConstraintResult]:
        """Fetch latest CSP validation result for a case."""
        result = await self.db.execute(
            select(ConstraintResult)
            .where(ConstraintResult.case_id == case_id)
            .order_by(ConstraintResult.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_violations(self, case_id: int) -> List[GraphValidation]:
        """Fetch list of graph violations for a case."""
        result = await self.db.execute(
            select(GraphValidation)
            .where(GraphValidation.case_id == case_id)
            .order_by(GraphValidation.created_at.desc())
        )
        return list(result.scalars().all())
