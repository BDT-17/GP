"""Tests for FastAPI Web Server endpoints."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post("/api/reset")
        yield c


def test_serve_index(client):
    """Test root endpoint serves HTML content."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "MASCOT" in response.text


def test_get_session(client):
    """Test getting initial session state."""
    response = client.get("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "concept_title" in data
    assert data["terminal_status"] == "active"
    assert data["active_role"] == "peer"


def test_chat_empty_message(client):
    """Test chat endpoint rejects empty message with HTTP 400."""
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
    assert "Tin nhắn không được để trống" in response.json()["detail"]


def test_chat_interaction_flow(client):
    """Test chat message processing and turn execution."""
    response = client.post(
        "/api/chat",
        json={"message": "Ghi đè là trong cùng 1 class hay khác class vậy bạn?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "session_state" in data
    assert "role" in data["reply"]
    assert "message" in data["reply"]
    assert "terminal" in data["reply"]


def test_get_summary(client):
    """Test getting instructor summary."""
    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "concept_id" in data
    assert "terminal_status" in data
    assert "citations_used" in data


def test_reset_session(client):
    """Test session reset endpoint."""
    response = client.post("/api/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "reset_successful"

