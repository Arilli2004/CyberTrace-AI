"""
Unit & Integration Tests for Evidence Normalization Engine
"""
import pytest
import pytest_asyncio
import io
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.connection import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models import User, UserRole, Case, CaseStatus, EventCategory, SeverityLevel
from app.normalization.rule_engine import NormalizationRuleEngine
from app.normalization.timestamp_converter import TimestampConverter
from app.normalization.field_mapper import FieldMapper

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
            name="Normalization Test Investigator",
            email="norm@cybertrace.ai",
            password_hash=hash_password("Password@123"),
            role=UserRole.investigator,
        )
        session.add(user)
        await session.commit()

        case = Case(
            id=1,
            title="Normalized Forensic Investigation",
            description="Testing normalization taxonomy and rule engine",
            investigator_id=1,
            status=CaseStatus.new,
            priority="critical",
        )
        session.add(case)
        await session.commit()

        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def auth_headers(test_db):
    token = create_access_token({"sub": "1", "role": "investigator"})
    return {"Authorization": f"Bearer {token}"}


# ─── Unit Tests ───────────────────────────────────────────────────────────────
def test_rule_engine_win_4624():
    category, action, severity = NormalizationRuleEngine.evaluate(
        raw_event_type="WindowsLog",
        event_id="4624",
        description="An account was successfully logged on",
        source="Security",
    )
    assert category == EventCategory.AUTHENTICATION
    assert action == "AUTH_SUCCESS"
    assert severity == SeverityLevel.low


def test_rule_engine_win_4625_critical():
    category, action, severity = NormalizationRuleEngine.evaluate(
        raw_event_type="WindowsLog",
        event_id="4625",
        description="An account failed to log on",
        source="Security",
    )
    assert category == EventCategory.AUTHENTICATION
    assert action == "AUTH_FAILURE"
    assert severity == SeverityLevel.critical


def test_rule_engine_log_cleared():
    category, action, severity = NormalizationRuleEngine.evaluate(
        raw_event_type="WindowsLog",
        event_id="1102",
        description="The audit log was cleared",
        source="Security",
    )
    assert category == EventCategory.DEFENSE_EVASION
    assert action == "LOG_CLEARED"
    assert severity == SeverityLevel.critical


def test_timestamp_converter_utc():
    naive_dt = datetime(2026, 8, 3, 12, 0, 0)
    utc_dt = TimestampConverter.to_utc(naive_dt)
    assert utc_dt.tzinfo == timezone.utc

    iso_str = "2026-08-03T12:00:00Z"
    parsed = TimestampConverter.to_utc(iso_str)
    assert parsed.tzinfo == timezone.utc


def test_field_mapper_domain_and_ip():
    extracted = FieldMapper.extract_fields(
        raw_event_dict={"user": "CORP\\jdoe"},
        description="Failed login attempt from IP 192.168.1.50",
    )
    assert extracted["domain"] == "CORP"
    assert extracted["username"] == "jdoe"
    assert extracted["ip_address"] == "192.168.1.50"


# ─── Integration & API Test ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_evidence_parse_and_normalize_api(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload CSV Evidence
        csv_data = b"timestamp,hostname,username,action,src_ip,severity,message\n2026-08-03T12:00:00Z,FS-01,CORP\\admin,LOGIN_OK,10.0.0.5,low,User logged in successfully\n"
        files = {"files": ("auth_log.csv", io.BytesIO(csv_data), "text/csv")}
        res1 = await client.post("/api/evidence/upload", files=files, data={"case_id": "1"}, headers=auth_headers)
        assert res1.status_code == 201
        evidence_id = res1.json()[0]["id"]

        # 2. Trigger Parser
        res2 = await client.post(f"/api/parser/parse/{evidence_id}", headers=auth_headers)
        assert res2.status_code == 202

        # 3. Trigger Normalization
        res3 = await client.post(f"/api/normalize/{evidence_id}", headers=auth_headers)
        assert res3.status_code == 202
        norm_res = res3.json()
        assert norm_res["event_count"] == 1
        assert norm_res["processing_stage"] == "NORMALIZED"

        # 4. Query Normalized Events for Case
        res4 = await client.get("/api/normalized-events/1", headers=auth_headers)
        assert res4.status_code == 200
        events_res = res4.json()
        assert events_res["total"] == 1
        record = events_res["events"][0]
        assert record["hostname"] == "FS-01"
        assert record["domain"] == "CORP"
        assert record["username"] == "admin"
        assert record["event_category"] == "Authentication"
        assert record["normalized"] is True

    app.dependency_overrides.clear()
