import os

import pytest
from httpx import ASGITransport, AsyncClient

# Use a short NATS timeout so tests don't hang when NATS is unavailable
os.environ.setdefault("NATS_TIMEOUT", "1")


@pytest.mark.asyncio
async def test_health_endpoint():
    from overmind_mail_bridge.server import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_webhook_accepts_valid_payload():
    from overmind_mail_bridge.server import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/webhook", json={
            "event": "store.ingest",
            "message": "From: alice@test\nTo: bob@test\nSubject: Hi\n\nHello",
        })
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_payload():
    from overmind_mail_bridge.server import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/webhook", json={"invalid": "data"})
    assert resp.status_code == 422
