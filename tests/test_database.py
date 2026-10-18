"""Tests for SQLite Database persistence and learner profile endpoints."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import app
from src.mascot.database import DatabaseManager


@pytest.fixture
def temp_db(tmp_path):
    """Fixture to provide a clean temporary SQLite database."""
    db_file = tmp_path / "test_mascot.db"
    return DatabaseManager(db_path=db_file)


def test_init_db_and_default_profile(temp_db):
    """Verify database initialization and default profile seeding."""
    profile = temp_db.get_learner_profile()
    assert profile["username"] == "QuocAnh162480"
    assert profile["display_name"] == "Quoc Anh"
    assert profile["xp"] == 568
    assert profile["gems"] == 772
    assert profile["streak"] == 1
    assert profile["hearts"] == 3


def test_update_learner_profile(temp_db):
    """Verify XP, gems, streak, and hearts updates."""
    updated = temp_db.update_learner_profile(
        xp_delta=50,
        gems_delta=15,
        streak_increment=True,
        hearts=2,
    )
    assert updated["xp"] == 568 + 50
    assert updated["gems"] == 772 + 15
    assert updated["streak"] == 2
    assert updated["hearts"] == 2


def test_session_persistence_lifecycle(temp_db):
    """Verify saving session, logging messages, and updating completion."""
    session_id = "test-session-123"

    # 1. Save session
    temp_db.save_or_update_session(
        session_id=session_id,
        course_id="CS102",
        concept_id="oop_polymorphism",
        terminal_status="active",
        learner_attempts=1,
    )

    # 2. Add chat turns
    temp_db.add_chat_message(session_id, "peer", "Nạp chồng với ghi đè là một đúng không?")
    temp_db.add_chat_message(session_id, "learner", "Không đúng, khác nhau.")
    temp_db.add_chat_message(session_id, "ta", "Gợi ý: chú ý phạm vi lớp.")

    history = temp_db.get_chat_history(session_id)
    assert len(history) == 3
    assert history[0]["role"] == "peer"
    assert history[1]["role"] == "learner"
    assert history[2]["role"] == "ta"

    # 3. Mark completed
    temp_db.save_or_update_session(
        session_id=session_id,
        course_id="CS102",
        concept_id="oop_polymorphism",
        terminal_status="completed",
        misconception_repaired=True,
        explain_back_passed=True,
        completed_at="2026-10-18T10:00:00Z",
    )

    all_sessions = temp_db.get_all_sessions()
    target_session = next(s for s in all_sessions if s["session_id"] == session_id)
    assert target_session["terminal_status"] == "completed"
    assert target_session["misconception_repaired"] == 1
    assert target_session["explain_back_passed"] == 1


def test_api_database_endpoints():
    """Verify REST API endpoints for profile, session history, and session list."""
    with TestClient(app) as client:
        # 1. GET /api/profile
        res_profile = client.get("/api/profile")
        assert res_profile.status_code == 200
        data_prof = res_profile.json()
        assert "username" in data_prof
        assert "xp" in data_prof
        assert "gems" in data_prof

        # 2. POST /api/profile/update
        res_update = client.post(
            "/api/profile/update",
            json={"xp_delta": 20, "gems_delta": 5, "streak_increment": False, "hearts": 3},
        )
        assert res_update.status_code == 200
        assert res_update.json()["xp"] >= data_prof["xp"] + 20

        # 3. GET /api/sessions
        res_sessions = client.get("/api/sessions")
        assert res_sessions.status_code == 200
        assert "sessions" in res_sessions.json()

        # 4. GET /api/session/{session_id}/history
        res_session = client.get("/api/session")
        session_id = res_session.json()["session_id"]
        res_hist = client.get(f"/api/session/{session_id}/history")
        assert res_hist.status_code == 200
        assert "history" in res_hist.json()
        assert len(res_hist.json()["history"]) >= 1

