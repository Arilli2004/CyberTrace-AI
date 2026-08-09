"""
Pytest Unit and Integration Tests for Module 10 — Forward Chaining Inference Engine
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.connection import Base, get_db
from app.models import User, UserRole, Case, CaseStatus, NormalizedEvent, EventCategory, SeverityLevel
from app.ai.forward_chaining import ForwardChainingEngine, Fact, get_standard_forensic_rules

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with TestingSessionLocal() as session:
        user = User(
            id=1,
            name="ForwardChaining Investigator",
            email="fc@cybertrace.ai",
            password_hash="hashed_pw",
            role=UserRole.investigator,
        )
        session.add(user)
        await session.commit()

        case = Case(
            id=1,
            title="Forward Chaining Ransomware Test Case",
            description="Testing automated data-driven threat reasoning",
            investigator_id=1,
            status=CaseStatus.analysis,
        )
        session.add(case)
        await session.commit()

        # Add Normalized Events for Case
        from datetime import datetime, timezone
        events = [
            NormalizedEvent(
                id=1, case_id=1, evidence_id=1,
                timestamp_utc=datetime.now(timezone.utc),
                hostname="FS-01", username="admin",
                action="AUTH_FAILED", severity=SeverityLevel.high,
                event_category=EventCategory.AUTHENTICATION
            ),
            NormalizedEvent(
                id=2, case_id=1, evidence_id=1,
                timestamp_utc=datetime.now(timezone.utc),
                hostname="FS-01", username="admin",
                action="AUTH_FAILED", severity=SeverityLevel.high,
                event_category=EventCategory.AUTHENTICATION
            ),
            NormalizedEvent(
                id=3, case_id=1, evidence_id=1,
                timestamp_utc=datetime.now(timezone.utc),
                hostname="FS-01", username="admin",
                action="AUTH_FAILED", severity=SeverityLevel.high,
                event_category=EventCategory.AUTHENTICATION
            ),
            NormalizedEvent(
                id=4, case_id=1, evidence_id=1,
                timestamp_utc=datetime.now(timezone.utc),
                hostname="FS-01", process_name="vssadmin.exe",
                command_line="vssadmin.exe delete shadows /all /quiet",
                action="PROCESS_CREATE", severity=SeverityLevel.critical,
                event_category=EventCategory.DEFENSE_EVASION
            )
        ]
        for e in events:
            session.add(e)
        await session.commit()

        yield session

    await engine.dispose()


# ─── Pure Unit Tests for ForwardChaining Engine ───────────────────────────────

def test_pure_forward_chaining_brute_force_rule():
    engine = ForwardChainingEngine()
    initial_facts = [
        Fact("F1", "AUTH_FAILURE_BURST", "AUTHENTICATION_SERVICE", "5_failures")
    ]
    res = engine.run_inference(initial_facts)

    assert res.total_facts_count > res.initial_facts_count
    assert len(res.fired_rules) >= 1
    fired_ids = [r.rule_id for r in res.fired_rules]
    assert "RULE_01_BRUTE_FORCE" in fired_ids
    derived_types = [d["fact_type"] for d in res.derived_facts]
    assert "SUSPECTED_BRUTE_FORCE" in derived_types


def test_pure_forward_chaining_ransomware_rule():
    engine = ForwardChainingEngine()
    initial_facts = [
        Fact("F1", "SHADOW_COPY_DELETION", "host:FS-01", "vssadmin.exe delete shadows")
    ]
    res = engine.run_inference(initial_facts)

    assert res.total_facts_count > res.initial_facts_count
    fired_ids = [r.rule_id for r in res.fired_rules]
    assert "RULE_03_RANSOMWARE" in fired_ids
    derived_types = [d["fact_type"] for d in res.derived_facts]
    assert "CRITICAL_THREAT" in derived_types


def test_pure_forward_chaining_wmi_lateral_movement():
    engine = ForwardChainingEngine()
    initial_facts = [
        Fact("F1", "PROCESS_CREATE", "host:DC-01", "powershell.exe"),
        Fact("F2", "WMI_EXECUTION", "host:DC-01", "wmiprvse.exe")
    ]
    res = engine.run_inference(initial_facts)

    fired_ids = [r.rule_id for r in res.fired_rules]
    assert "RULE_02_WMI_LATERAL" in fired_ids


# ─── Integration & API Endpoint Tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_forward_chaining_normal_case(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "case_id": 1,
            "custom_facts": [
                {
                    "fact_type": "MASS_FILE_RENAME",
                    "entity": "host:FS-01",
                    "value": "encrypted_2000_files"
                }
            ]
        }
        res = await client.post("/api/v1/ai/forward-chaining/run", json=payload)
        assert res.status_code == 200

        data = res.json()
        assert data["success"] is True
        assert data["case_id"] == 1
        assert data["initial_facts_count"] >= 4
        assert len(data["fired_rules"]) >= 1
        assert "execution_time_ms" in data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_forward_chaining_case_not_found(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "case_id": 999999
        }
        res = await client.post("/api/v1/ai/forward-chaining/run", json=payload)
        assert res.status_code == 404
        assert "Case with ID 999999 not found" in res.json()["detail"]

    app.dependency_overrides.clear()
