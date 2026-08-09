"""
Unit & API Tests for Evidence Management Module
"""
import pytest
import pytest_asyncio
import io
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.connection import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models import User, UserRole, Case, CaseStatus

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with TestingSessionLocal() as session:
        # Seed test user
        user = User(
            id=1,
            name="Test Investigator",
            email="test@cybertrace.ai",
            password_hash=hash_password("Password@123"),
            role=UserRole.investigator,
        )
        session.add(user)
        await session.commit()

        # Seed test case
        case = Case(
            id=1,
            title="Forensic Malware Investigation",
            description="Investigating suspicious process execution",
            investigator_id=1,
            status=CaseStatus.new,
            priority="high",
        )
        session.add(case)
        await session.commit()

        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def auth_headers(test_db):
    token = create_access_token({"sub": "1", "role": "investigator"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_evidence_upload_and_hashing(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        log_content = b"2026-08-03 12:00:00 [SECURITY] Failed login attempt from IP 192.168.1.50\n"
        files = {"files": ("syslog.log", io.BytesIO(log_content), "text/plain")}
        data = {"case_id": "1"}

        res = await client.post("/api/evidence/upload", files=files, data=data, headers=auth_headers)
        assert res.status_code == 201
        uploaded = res.json()
        assert len(uploaded) == 1
        record = uploaded[0]
        assert record["original_filename"] == "syslog.log"
        assert record["sha256"] is not None
        assert record["sha1"] is not None
        assert record["md5"] is not None
        assert record["verification_status"] == "verified"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_executable_file_rejection(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload_content = b"MZ\x90\x00\x03\x00\x00\x00"  # Fake PE binary
        files = {"files": ("malware.exe", io.BytesIO(payload_content), "application/octet-stream")}
        data = {"case_id": "1"}

        res = await client.post("/api/evidence/upload", files=files, data=data, headers=auth_headers)
        assert res.status_code == 400
        assert "Executable and script file types" in res.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_duplicate_hash_rejection(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        log_content = b"Exact Duplicate Log Data Content 12345\n"

        # 1st Upload
        files1 = {"files": ("sample1.log", io.BytesIO(log_content), "text/plain")}
        res1 = await client.post("/api/evidence/upload", files=files1, data={"case_id": "1"}, headers=auth_headers)
        assert res1.status_code == 201

        # 2nd Upload with identical hash
        files2 = {"files": ("sample2.log", io.BytesIO(log_content), "text/plain")}
        res2 = await client.post("/api/evidence/upload", files=files2, data={"case_id": "1"}, headers=auth_headers)
        assert res2.status_code == 409
        assert "Duplicate Evidence Error" in res2.json()["detail"]

    app.dependency_overrides.clear()
