"""
Pytest Unit and Integration Tests for Module 8 — Uniform Cost Search (UCS) Engine
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.connection import Base, get_db
from app.models import User, UserRole, Case, CaseStatus, GraphNode, GraphEdge
from app.ai.uniform_cost_search import UniformCostSearch

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with TestingSessionLocal() as session:
        # Create Test User
        user = User(
            id=1,
            name="UCS Investigator",
            email="ucs@cybertrace.ai",
            password_hash="hashed_pw",
            role=UserRole.investigator,
        )
        session.add(user)
        await session.commit()

        # Create Test Case
        case = Case(
            id=1,
            title="UCS Path Reconstruction Test Case",
            description="Testing Uniform Cost Search on Knowledge Graph",
            investigator_id=1,
            status=CaseStatus.analysis,
        )
        session.add(case)
        await session.commit()

        # Create Knowledge Graph Nodes
        nodes = [
            GraphNode(id=1, case_id=1, node_type="Event", node_label="login"),
            GraphNode(id=2, case_id=1, node_type="Event", node_label="usb_insert"),
            GraphNode(id=3, case_id=1, node_type="Event", node_label="file_copy"),
            GraphNode(id=4, case_id=1, node_type="Event", node_label="usb_remove"),
            GraphNode(id=5, case_id=1, node_type="Event", node_label="isolated_exfil"),
            GraphNode(id=6, case_id=1, node_type="Event", node_label="alt_pivot"),
        ]
        for n in nodes:
            session.add(n)
        await session.commit()

        # Create Knowledge Graph Edges
        # Path 1: login (1) -> usb_insert (2) -> file_copy (3) -> usb_remove (4) (costs: 1.0 + 1.0 + 1.0 = 3.0)
        # Path 2 (Alternative higher cost): login (1) -> alt_pivot (6) -> usb_remove (4) (costs: 5.0 + 5.0 = 10.0)
        edges = [
            GraphEdge(id=1, case_id=1, source_node_id=1, destination_node_id=2, edge_type="THEN", weight=1.0),
            GraphEdge(id=2, case_id=1, source_node_id=2, destination_node_id=3, edge_type="THEN", weight=1.0),
            GraphEdge(id=3, case_id=1, source_node_id=3, destination_node_id=4, edge_type="THEN", weight=1.0),
            GraphEdge(id=4, case_id=1, source_node_id=1, destination_node_id=6, edge_type="ALT_PATH", weight=5.0),
            GraphEdge(id=5, case_id=1, source_node_id=6, destination_node_id=4, edge_type="ALT_PATH", weight=5.0),
        ]
        for e in edges:
            session.add(e)
        await session.commit()

        yield session

    await engine.dispose()


# ─── Pure Unit Tests for UniformCostSearch Engine ────────────────────────────

def test_pure_ucs_normal_path():
    adj = {
        "login": [("usb_insert", 1.0), ("alt_pivot", 5.0)],
        "usb_insert": [("file_copy", 1.0)],
        "file_copy": [("usb_remove", 1.0)],
        "alt_pivot": [("usb_remove", 5.0)],
        "usb_remove": [],
    }
    engine = UniformCostSearch(adj)
    res = engine.search("login", "usb_remove")

    assert res.is_path_found is True
    assert res.path == ["login", "usb_insert", "file_copy", "usb_remove"]
    assert res.total_cost == 3.0
    assert res.visited_nodes_count >= 4
    assert res.execution_time_ms >= 0.0


def test_pure_ucs_single_node():
    adj = {"login": [("usb_insert", 1.0)]}
    engine = UniformCostSearch(adj)
    res = engine.search("login", "login")

    assert res.is_path_found is True
    assert res.path == ["login"]
    assert res.total_cost == 0.0
    assert res.visited_nodes_count == 1


def test_pure_ucs_no_path_disconnected():
    adj = {
        "login": [("usb_insert", 1.0)],
        "usb_insert": [],
        "isolated_exfil": []
    }
    engine = UniformCostSearch(adj)
    res = engine.search("login", "isolated_exfil")

    assert res.is_path_found is False
    assert res.path == []
    assert res.total_cost == float("inf")


def test_pure_ucs_multiple_paths_chooses_minimum_cost():
    # Path A: A -> B (2.0) -> D (3.0) = 5.0
    # Path B: A -> C (1.0) -> D (1.5) = 2.5 (Cheaper)
    adj = {
        "A": [("B", 2.0), ("C", 1.0)],
        "B": [("D", 3.0)],
        "C": [("D", 1.5)],
        "D": []
    }
    engine = UniformCostSearch(adj)
    res = engine.search("A", "D")

    assert res.is_path_found is True
    assert res.path == ["A", "C", "D"]
    assert res.total_cost == 2.5


# ─── Integration & API Endpoint Tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_ucs_normal_path(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "case_id": 1,
            "start_node": "login",
            "goal_node": "usb_remove"
        }
        res = await client.post("/api/v1/ai/ucs/run", json=payload)
        assert res.status_code == 200

        data = res.json()
        assert data["success"] is True
        assert data["path"] == ["login", "usb_insert", "file_copy", "usb_remove"]
        assert data["total_cost"] == 3.0
        assert data["visited_nodes"] >= 4
        assert "execution_time_ms" in data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_ucs_no_path_exists(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "case_id": 1,
            "start_node": "login",
            "goal_node": "isolated_exfil"
        }
        res = await client.post("/api/v1/ai/ucs/run", json=payload)
        assert res.status_code == 400
        assert "No valid path exists" in res.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_ucs_invalid_start_node(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "case_id": 1,
            "start_node": "non_existent_start",
            "goal_node": "usb_remove"
        }
        res = await client.post("/api/v1/ai/ucs/run", json=payload)
        assert res.status_code == 404
        assert "Start node 'non_existent_start' not found" in res.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_ucs_invalid_goal_node(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "case_id": 1,
            "start_node": "login",
            "goal_node": "non_existent_goal"
        }
        res = await client.post("/api/v1/ai/ucs/run", json=payload)
        assert res.status_code == 404
        assert "Goal node 'non_existent_goal' not found" in res.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_ucs_case_not_found(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "case_id": 999999,
            "start_node": "login",
            "goal_node": "usb_remove"
        }
        res = await client.post("/api/v1/ai/ucs/run", json=payload)
        assert res.status_code == 404
        assert "Case with ID 999999 not found" in res.json()["detail"]

    app.dependency_overrides.clear()
