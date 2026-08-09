"""
Pytest Unit and Integration Tests for Module 9 — A* Search Algorithm Engine
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.connection import Base, get_db
from app.models import User, UserRole, Case, CaseStatus, GraphNode, GraphEdge
from app.ai.astar_search import AStarSearch, HopDistanceHeuristic, DefaultZeroHeuristic

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
            name="A* Investigator",
            email="astar@cybertrace.ai",
            password_hash="hashed_pw",
            role=UserRole.investigator,
        )
        session.add(user)
        await session.commit()

        # Create Test Case
        case = Case(
            id=1,
            title="A* Path Reconstruction Test Case",
            description="Testing A* Search on Knowledge Graph",
            investigator_id=1,
            status=CaseStatus.analysis,
        )
        session.add(case)
        await session.commit()

        # Create Knowledge Graph Nodes
        nodes = [
            GraphNode(id=1, case_id=1, node_type="Event", node_label="login", properties={"privilege_level": 1}),
            GraphNode(id=2, case_id=1, node_type="Event", node_label="usb_insert", properties={"privilege_level": 1}),
            GraphNode(id=3, case_id=1, node_type="Event", node_label="file_copy", properties={"privilege_level": 2}),
            GraphNode(id=4, case_id=1, node_type="Event", node_label="usb_remove", properties={"privilege_level": 3}),
            GraphNode(id=5, case_id=1, node_type="Event", node_label="isolated_exfil", properties={"privilege_level": 1}),
            GraphNode(id=6, case_id=1, node_type="Event", node_label="alt_pivot", properties={"privilege_level": 1}),
        ]
        for n in nodes:
            session.add(n)
        await session.commit()

        # Create Knowledge Graph Edges
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


# ─── Pure Unit Tests for AStarSearch Engine ───────────────────────────────────

def test_pure_astar_normal_path():
    adj = {
        "login": [("usb_insert", 1.0), ("alt_pivot", 5.0)],
        "usb_insert": [("file_copy", 1.0)],
        "file_copy": [("usb_remove", 1.0)],
        "alt_pivot": [("usb_remove", 5.0)],
        "usb_remove": [],
    }
    props = {
        "login": {"privilege_level": 1},
        "usb_insert": {"privilege_level": 1},
        "file_copy": {"privilege_level": 2},
        "usb_remove": {"privilege_level": 3},
        "alt_pivot": {"privilege_level": 1},
    }
    engine = AStarSearch(adj, heuristic=HopDistanceHeuristic(), node_properties=props)
    res = engine.search("login", "usb_remove")

    assert res.is_path_found is True
    assert res.path == ["login", "usb_insert", "file_copy", "usb_remove"]
    assert res.total_cost == 3.0
    assert res.heuristic_cost == 1.0  # (3 - 1) * 0.5
    assert res.visited_nodes_count <= 4
    assert res.execution_time_ms >= 0.0


def test_pure_astar_single_node():
    adj = {"login": [("usb_insert", 1.0)]}
    engine = AStarSearch(adj)
    res = engine.search("login", "login")

    assert res.is_path_found is True
    assert res.path == ["login"]
    assert res.total_cost == 0.0
    assert res.visited_nodes_count == 1


def test_pure_astar_no_path_disconnected():
    adj = {
        "login": [("usb_insert", 1.0)],
        "usb_insert": [],
        "isolated_exfil": []
    }
    engine = AStarSearch(adj)
    res = engine.search("login", "isolated_exfil")

    assert res.is_path_found is False
    assert res.path == []
    assert res.total_cost == float("inf")


def test_pure_astar_equal_cost_and_large_graph():
    # Construct a 20-node linear chain graph with a noisy secondary branch
    adj = {f"N{i}": [(f"N{i+1}", 1.0)] for i in range(1, 20)}
    adj["N20"] = []
    # Add noisy high cost shortcuts
    adj["N1"].append(("N10", 15.0))

    engine = AStarSearch(adj, heuristic=DefaultZeroHeuristic())
    res = engine.search("N1", "N20")

    assert res.is_path_found is True
    assert len(res.path) == 20
    assert res.total_cost == 19.0


# ─── Integration & API Endpoint Tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_astar_normal_path(test_db):
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
        res = await client.post("/api/v1/ai/astar/run", json=payload)
        assert res.status_code == 200

        data = res.json()
        assert data["success"] is True
        assert data["path"] == ["login", "usb_insert", "file_copy", "usb_remove"]
        assert data["total_cost"] == 3.0
        assert "heuristic_cost" in data
        assert data["visited_nodes"] <= 4
        assert "execution_time_ms" in data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_astar_no_path_exists(test_db):
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
        res = await client.post("/api/v1/ai/astar/run", json=payload)
        assert res.status_code == 400
        assert "No valid path exists" in res.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_astar_invalid_start_node(test_db):
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
        res = await client.post("/api/v1/ai/astar/run", json=payload)
        assert res.status_code == 404
        assert "Start node 'non_existent_start' not found" in res.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_astar_invalid_goal_node(test_db):
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
        res = await client.post("/api/v1/ai/astar/run", json=payload)
        assert res.status_code == 404
        assert "Goal node 'non_existent_goal' not found" in res.json()["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_astar_case_not_found(test_db):
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
        res = await client.post("/api/v1/ai/astar/run", json=payload)
        assert res.status_code == 404
        assert "Case with ID 999999 not found" in res.json()["detail"]

    app.dependency_overrides.clear()
