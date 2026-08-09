"""
Unit & API Tests for Case Management System
"""
import pytest
import pytest_asyncio
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

        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def auth_headers(test_db):
    token = create_access_token({"sub": "1", "role": "investigator"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_case_api(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "Suspicious Intrusion Alert",
            "description": "Exfiltration attempt on web server",
            "priority": "high",
        }
        res = await client.post("/api/cases/", json=payload, headers=auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == payload["title"]
        assert data["priority"] == "high"
        assert data["status"] == "new"
        assert data["uuid_id"] is not None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_and_filter_cases(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # Insert sample case
    case = Case(
        title="Malware Analysis Unit",
        description="Trojan binary dropped in Temp directory",
        investigator_id=1,
        priority="critical",
        status=CaseStatus.new,
    )
    test_db.add(case)
    await test_db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/cases/?search=Malware", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["cases"][0]["title"] == "Malware Analysis Unit"

    app.dependency_overrides.clear()
