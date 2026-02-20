"""Tests for API endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from main import app
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "brands" in data
    assert "ticket99" in data["brands"]
    assert "eventitans" in data["brands"]


def test_ticket99_chat(client):
    resp = client.post("/api/ticket99/chat", json={
        "message": "hello",
        "sessionId": None,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "message" in data
    assert len(data["message"]) > 0
    assert "sessionId" in data


def test_eventitans_chat(client):
    resp = client.post("/api/eventitans/chat", json={
        "message": "what are your pricing plans?",
        "sessionId": None,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["message"]) > 0


def test_chat_empty_message(client):
    resp = client.post("/api/ticket99/chat", json={
        "message": "",
        "sessionId": None,
    })
    assert resp.status_code == 400


def test_leads_endpoint(client):
    resp = client.post("/api/leads", json={
        "name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "type": "organizer",
        "brand": "ticket99",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_clear_endpoint(client):
    # First create a session
    resp = client.post("/api/ticket99/chat", json={
        "message": "hello",
        "sessionId": "test_clear_session",
    })
    data = resp.json()
    session_id = data["sessionId"]

    # Clear it
    resp = client.post("/api/clear", json={"sessionId": session_id})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_demo_page(client):
    resp = client.get("/demo")
    assert resp.status_code == 200
    assert "Dual-Brand" in resp.text
