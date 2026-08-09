"""
Unit & Integration Tests for Multi-Format Parser Engine
"""
import pytest
import pytest_asyncio
import io
import zipfile
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.connection import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models import User, UserRole, Case, CaseStatus
from app.parsers.evtx_parser import EvtxParser
from app.parsers.linux_parser import LinuxParser
from app.parsers.csv_parser import CsvParser
from app.parsers.json_parser import JsonParser
from app.parsers.xml_parser import XmlParser
from app.parsers.zip_parser import ZipParser

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
            name="Parser Test Investigator",
            email="parser@cybertrace.ai",
            password_hash=hash_password("Password@123"),
            role=UserRole.investigator,
        )
        session.add(user)
        await session.commit()

        case = Case(
            id=1,
            title="Log Parser Investigation Case",
            description="Testing multi-format evidence ingestion and parsing",
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
def test_linux_auth_log_parser(tmp_path):
    log_file = tmp_path / "auth.log"
    log_file.write_text(
        "Aug  3 12:00:00 server01 sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 22 ssh2\n"
        "Aug  3 12:01:00 server01 sshd[1235]: Accepted password for root from 192.168.1.100 port 22 ssh2\n"
    )

    parser = LinuxParser()
    events = parser.parse(str(log_file))

    assert len(events) == 2
    assert events[0]["severity"] == "critical"
    assert events[0]["event_type"] == "AuthFailure"
    assert events[0]["user"] == "admin"
    assert events[0]["ip_address"] == "192.168.1.100"
    assert events[1]["severity"] == "high"
    assert events[1]["event_type"] == "AuthSuccess"


def test_csv_log_parser(tmp_path):
    csv_file = tmp_path / "firewall.csv"
    csv_file.write_text(
        "timestamp,hostname,username,action,src_ip,severity,message\n"
        "2026-08-03T12:00:00Z,FW-01,operator,PortScan,10.0.0.5,high,Port scan detected on subnet\n"
    )

    parser = CsvParser()
    events = parser.parse(str(csv_file))

    assert len(events) == 1
    assert events[0]["host"] == "FW-01"
    assert events[0]["user"] == "operator"
    assert events[0]["ip_address"] == "10.0.0.5"
    assert events[0]["severity"] == "high"


def test_json_log_parser(tmp_path):
    json_file = tmp_path / "audit.json"
    json_file.write_text(
        '{"timestamp": "2026-08-03T12:30:00Z", "hostname": "DB-01", "username": "dbadmin", "event_type": "SchemaChange", "severity": "critical", "description": "Table dropped"}\n'
    )

    parser = JsonParser()
    events = parser.parse(str(json_file))

    assert len(events) == 1
    assert events[0]["host"] == "DB-01"
    assert events[0]["user"] == "dbadmin"
    assert events[0]["event_type"] == "SchemaChange"
    assert events[0]["severity"] == "critical"


def test_evtx_xml_parser(tmp_path):
    xml_file = tmp_path / "security.xml"
    xml_content = """
    <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System>
        <Provider Name="Microsoft-Windows-Security-Auditing"/>
        <EventID>4625</EventID>
        <Computer>DC-01.corp.local</Computer>
      </System>
      <EventData>
        <Data Name="TargetUserName">TargetUser</Data>
        <Data Name="IpAddress">172.16.0.45</Data>
      </EventData>
    </Event>
    """
    xml_file.write_text(xml_content)

    parser = EvtxParser()
    events = parser.parse(str(xml_file))

    assert len(events) == 1
    assert events[0]["event_id"] == "4625"
    assert events[0]["host"] == "DC-01.corp.local"
    assert events[0]["user"] == "TargetUser"
    assert events[0]["severity"] == "critical"


# ─── Integration & API Test ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_evidence_upload_and_parse_api(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload CSV log evidence
        csv_data = b"timestamp,hostname,username,action,src_ip,severity,message\n2026-08-03T12:00:00Z,DC-01,admin,UserLogin,192.168.1.1,medium,User login successful\n"
        files = {"files": ("auth_audit.csv", io.BytesIO(csv_data), "text/csv")}
        res1 = await client.post("/api/evidence/upload", files=files, data={"case_id": "1"}, headers=auth_headers)
        assert res1.status_code == 201
        evidence_id = res1.json()[0]["id"]

        # 2. Trigger parse API
        res2 = await client.post(f"/api/parser/parse/{evidence_id}", headers=auth_headers)
        assert res2.status_code == 202
        parsed_res = res2.json()
        assert parsed_res["event_count"] == 1
        assert parsed_res["processing_stage"] == "PARSED"

        # 3. Query parsed events for case
        res3 = await client.get("/api/parser/events/case/1", headers=auth_headers)
        assert res3.status_code == 200
        events_res = res3.json()
        assert events_res["total"] == 1
        assert events_res["events"][0]["host"] == "DC-01"

    app.dependency_overrides.clear()
