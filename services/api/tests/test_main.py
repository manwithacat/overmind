import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from overmind_api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_persons_graceful_without_db(client):
    """Without a DB connection, persons endpoint returns empty with error."""
    resp = await client.get("/api/v1/graph/persons")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert isinstance(data["persons"], list)


@pytest.mark.asyncio
async def test_person_connections_graceful_without_db(client):
    resp = await client.get("/api/v1/graph/persons/test@example.com/connections")
    assert resp.status_code == 200
    data = resp.json()
    assert data["person"] == "test@example.com"
    assert isinstance(data["sends_to"], list)
    assert isinstance(data["receives_from"], list)


@pytest.mark.asyncio
async def test_threads_graceful_without_db(client):
    resp = await client.get("/api/v1/graph/threads")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert isinstance(data["messages"], list)


@pytest.mark.asyncio
async def test_attention_cost_graceful_without_db(client):
    resp = await client.get("/api/v1/metrics/attention-cost")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_density_graceful_without_db(client):
    resp = await client.get("/api/v1/metrics/density")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert isinstance(data["buckets"], list)


@pytest.mark.asyncio
async def test_automation_graceful_without_db(client):
    resp = await client.get("/api/v1/metrics/automation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert isinstance(data["candidates"], list)


@pytest.mark.asyncio
async def test_message_types_graceful_without_db(client):
    resp = await client.get("/api/v1/metrics/message-types")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert isinstance(data["types"], list)


@pytest.mark.asyncio
async def test_sentiment_graceful_without_db(client):
    resp = await client.get("/api/v1/metrics/sentiment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert isinstance(data["sentiments"], list)


@pytest.mark.asyncio
async def test_threads_pagination(client):
    resp = await client.get("/api/v1/graph/threads?limit=10&offset=0")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_threads_invalid_limit(client):
    resp = await client.get("/api/v1/graph/threads?limit=0")
    assert resp.status_code == 422  # FastAPI validation error
