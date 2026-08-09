"""
Unit & Integration Tests for Enterprise CSP Constraint Engine (Backtracking)
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
from app.models import User, UserRole, Case, CaseStatus, GraphNode, GraphEdge
from app.reasoning.csp.constraint_rules import ProcessTreeRule, AuthSessionRule
from app.reasoning.csp.backtracking_engine import BacktrackingEngine
from app.reasoning.csp.csp_solver import CSPSolver

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
            name="CSP Test Investigator",
            email="csp@cybertrace.ai",
            password_hash=hash_password("Password@123"),
            role=UserRole.investigator,
        )
        session.add(user)
        await session.commit()

        case = Case(
            id=1,
            title="CSP Backtracking Validation Case",
            description="Testing constraint satisfaction engine and backtracking resolution",
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
def test_process_tree_rule():
    node = GraphNode(id=1, node_type="Process", node_label="powershell.exe")
    edge = GraphEdge(id=10, source_node_id=None, destination_node_id=1, edge_type="SPAWNED")

    rule = ProcessTreeRule()
    is_valid, reason, suggestion = rule.evaluate(node, [edge])
    assert is_valid is False
    assert "Orphan process" in reason


def test_backtracking_engine_auto_resolution():
    node = GraphNode(id=1, node_type="Process", node_label="cmd.exe")
    edge = GraphEdge(id=10, source_node_id=None, destination_node_id=1, edge_type="SPAWNED")

    engine = BacktrackingEngine()
    result = engine.solve([node], [edge])

    assert result["validation_status"] == "PASSED"  # Auto-resolved via backtracking
    assert result["resolved_count"] == 1
    assert result["validation_score"] == 100.0


# ─── Integration & API Test ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_full_csp_validation_api_pipeline(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup Evidence -> Parse -> Normalize -> Build Graph
        csv_data = b"timestamp,hostname,username,action,src_ip,severity,message\n2026-08-03T12:00:00Z,DC-01,CORP\\admin,LOGIN_OK,10.0.0.5,high,User logged in\n"
        files = {"files": ("auth_audit.csv", io.BytesIO(csv_data), "text/csv")}
        res1 = await client.post("/api/evidence/upload", files=files, data={"case_id": "1"}, headers=auth_headers)
        evidence_id = res1.json()[0]["id"]

        await client.post(f"/api/parser/parse/{evidence_id}", headers=auth_headers)
        await client.post(f"/api/normalize/{evidence_id}", headers=auth_headers)
        await client.post("/api/graph/build/1", headers=auth_headers)

        # 2. Trigger CSP Validation
        res2 = await client.post("/api/csp/validate/1", headers=auth_headers)
        assert res2.status_code == 202
        val_res = res2.json()
        assert val_res["validation_status"] in ("PASSED", "PARTIAL")
        assert val_res["validation_score"] >= 80.0

        # 3. Query Validation Status
        res3 = await client.get("/api/csp/status/1", headers=auth_headers)
        assert res3.status_code == 200
        assert res3.json()["validation_score"] >= 80.0

        # 4. Query Validation Detailed Results
        res4 = await client.get("/api/csp/results/1", headers=auth_headers)
        assert res4.status_code == 200
        assert res4.json()["result"]["case_id"] == 1

    app.dependency_overrides.clear()
