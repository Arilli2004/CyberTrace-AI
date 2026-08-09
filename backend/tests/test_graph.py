"""
Unit & Integration Tests for Enterprise Evidence Knowledge Graph Engine
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
from app.models import User, UserRole, Case, CaseStatus, EventCategory, SeverityLevel, NormalizedEvent
from app.graph.graph_taxonomy import NodeType, EdgeType
from app.graph.entity_extractor import EntityExtractor
from app.graph.relationship_extractor import RelationshipExtractor
from app.graph.node_deduplicator import NodeDeduplicator
from app.graph.weight_calculator import WeightCalculator
from app.graph.knowledge_graph_builder import KnowledgeGraphBuilder

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
            name="Graph Test Investigator",
            email="graph@cybertrace.ai",
            password_hash=hash_password("Password@123"),
            role=UserRole.investigator,
        )
        session.add(user)
        await session.commit()

        case = Case(
            id=1,
            title="Knowledge Graph Investigation Case",
            description="Testing graph topology construction and edge weighting",
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
def test_entity_extractor():
    event = NormalizedEvent(
        uuid_id="11111111-1111-1111-1111-111111111111",
        case_id=1,
        evidence_id=1,
        timestamp_utc=datetime.now(timezone.utc),
        hostname="DC-01",
        username="admin",
        domain="CORP",
        ip_address="10.0.0.5",
        process_name="powershell.exe",
        parent_process="cmd.exe",
        event_category=EventCategory.PROCESS_EXECUTION,
        severity=SeverityLevel.high,
        action="PROCESS_CREATE",
    )

    nodes = EntityExtractor.extract_nodes(event)
    labels = [n[1] for n in nodes]
    assert "DC-01" in labels
    assert "CORP\\admin" in labels
    assert "10.0.0.5" in labels
    assert "powershell.exe" in labels
    assert "cmd.exe" in labels


def test_node_deduplicator():
    dedup = NodeDeduplicator()
    node1, is_new1 = dedup.get_or_register(NodeType.HOST, "DC-01", {"ip": "10.0.0.5"}, case_id=1)
    node2, is_new2 = dedup.get_or_register(NodeType.HOST, "DC-01", {"domain": "CORP"}, case_id=1)

    assert is_new1 is True
    assert is_new2 is False
    assert node1.uuid_id == node2.uuid_id
    assert len(dedup.get_all_nodes()) == 1


def test_weight_calculator():
    critical_weight = WeightCalculator.calculate_weight(SeverityLevel.critical, confidence=0.9)
    low_weight = WeightCalculator.calculate_weight(SeverityLevel.low, confidence=0.9)

    assert critical_weight < low_weight  # Shortest path attractor for A*/UCS


# ─── Integration & API Test ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_full_knowledge_graph_api_pipeline(test_db, auth_headers):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload Evidence
        csv_data = b"timestamp,hostname,username,action,src_ip,severity,message\n2026-08-03T12:00:00Z,DC-01,CORP\\admin,LOGIN_OK,10.0.0.5,high,User logged in\n"
        files = {"files": ("auth_audit.csv", io.BytesIO(csv_data), "text/csv")}
        res1 = await client.post("/api/evidence/upload", files=files, data={"case_id": "1"}, headers=auth_headers)
        assert res1.status_code == 201
        evidence_id = res1.json()[0]["id"]

        # 2. Parse & Normalize Evidence
        await client.post(f"/api/parser/parse/{evidence_id}", headers=auth_headers)
        await client.post(f"/api/normalize/{evidence_id}", headers=auth_headers)

        # 3. Build Case Knowledge Graph
        res3 = await client.post("/api/graph/build/1", headers=auth_headers)
        assert res3.status_code == 202
        graph_build_res = res3.json()
        assert graph_build_res["node_count"] > 0
        assert graph_build_res["edge_count"] > 0
        assert graph_build_res["processing_stage"] == "GRAPH_CREATED"

        # 4. Query Case Knowledge Graph
        res4 = await client.get("/api/graph/1", headers=auth_headers)
        assert res4.status_code == 200
        graph_payload = res4.json()
        assert len(graph_payload["nodes"]) > 0
        assert len(graph_payload["edges"]) > 0

        # 5. Query Graph Statistics
        res5 = await client.get("/api/graph/statistics/1", headers=auth_headers)
        assert res5.status_code == 200
        stats = res5.json()
        assert stats["node_count"] > 0

    app.dependency_overrides.clear()
