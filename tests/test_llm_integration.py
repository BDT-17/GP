"""Tests for Multi-Provider LLM Client and Agent Integration."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

# Ensure root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import app
from src.mascot.agents import LecturerAgent, PeerAgent, TeachingAssistantAgent
from src.mascot.llm_client import LLMClient
from src.mascot.models import Citation


def test_llm_client_fallback_when_no_keys(monkeypatch):
    """Verify LLMClient defaults to fallback mode when no environment keys are present."""
    for key in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "OLLAMA_BASE_URL"]:
        monkeypatch.delenv(key, raising=False)

    client = LLMClient()
    assert client.get_provider() == "fallback"
    assert client.generate([{"role": "user", "content": "Hello"}]) is None


def test_llm_client_provider_detection(monkeypatch):
    """Verify provider detection precedence."""
    # Test Groq detection
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test123")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert LLMClient().get_provider() == "groq"

    # Test Gemini detection (takes precedence)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini_test123")
    assert LLMClient().get_provider() == "gemini"


def test_ta_agent_with_mocked_llm():
    """Verify TeachingAssistantAgent formats LLM Socratic hints correctly."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.get_provider.return_value = "gemini"
    mock_llm.generate.return_value = "Bạn hãy thử tự hỏi xem hai phương thức này có thể cùng tồn tại trong 1 lớp không?"

    ta = TeachingAssistantAgent(llm_client=mock_llm)
    hint = ta.get_hint(hint_level=1, learner_input="Tớ không biết", concept_title="OOP Polymorphism")

    assert "Gợi ý 1/2" in hint
    assert "hai phương thức này có thể cùng tồn tại trong 1 lớp không?" in hint
    mock_llm.generate.assert_called_once()


def test_ta_agent_fallback_when_llm_fails():
    """Verify TA degrades gracefully to deterministic hint when LLM returns None."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.get_provider.return_value = "gemini"
    mock_llm.generate.return_value = None  # API timeout / error

    ta = TeachingAssistantAgent(llm_client=mock_llm)
    hint = ta.get_hint(hint_level=1, learner_input="Help")

    # Should fall back to standard template
    assert "Hãy chú ý đến phạm vi xuất hiện của chúng" in hint


def test_peer_agent_with_mocked_llm():
    """Verify PeerAgent formats LLM repair acknowledgement correctly."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.get_provider.return_value = "groq"
    mock_llm.generate.return_value = "Cảm ơn cậu nhé, giờ tớ mới hiểu ra! Cậu có thể nói lại một lượt để tớ nhớ lâu không?"

    peer = PeerAgent(name="Bảo (Bạn học)", initial_misconception="abc", llm_client=mock_llm)
    reply = peer.acknowledge_repair(topic="Tính đa hình", learner_input="Overloading trong cùng 1 lớp nhé")

    assert "[Bảo (Bạn học)]:" in reply
    assert "Cảm ơn cậu nhé" in reply


def test_lecturer_agent_with_mocked_llm():
    """Verify LecturerAgent formats LLM explanation and appends citations."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.get_provider.return_value = "openai"
    mock_llm.generate.return_value = "Tôi xin tóm tắt: Nạp chồng là đa hình tĩnh, Ghi đè là đa hình động."

    lecturer = LecturerAgent(llm_client=mock_llm)
    citation = Citation(
        source_id="slide_1",
        source_location="Slide 2, Mục 2.1",
        chunk_id="c1",
        reference_snippet="Tính đa hình...",
    )
    res = lecturer.provide_clarification([citation], concept_title="Đa hình", learner_input="Thầy giải thích giúp em")

    assert "Tôi xin tóm tắt" in res
    assert "Slide 2, Mục 2.1" in res
    assert "Trích dẫn tài liệu" in res


def test_api_llm_status():
    """Verify /api/llm/status endpoint response."""
    with TestClient(app) as client:
        res = client.get("/api/llm/status")
        assert res.status_code == 200
        data = res.json()
        assert "provider" in data
        assert "is_live_llm" in data

