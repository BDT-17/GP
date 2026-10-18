"""Unit tests for Peer deliberation/pushback and Rubric-diagnostic LLM prompting."""

import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mascot.agents import PeerAgent, TeachingAssistantAgent
from mascot.llm_client import LLMClient
from mascot.models import Role, TerminalStatus
from mascot.orchestrator import MascotOrchestrator


def test_peer_pushback_on_unproven_challenge():
    """Peer pushes back when learner challenges without full technical proof."""
    orchestrator = MascotOrchestrator()
    orchestrator.start_session()

    # Learner challenges peer directly: "Cậu sai rồi Bảo ơi!"
    result = orchestrator.process_turn("Cậu sai rồi Bảo ơi!")

    assert result["role"] == Role.PEER.value
    assert orchestrator.peer_pushback_count == 1
    assert orchestrator.misconception_repaired is False
    assert orchestrator.terminal_status == TerminalStatus.ACTIVE
    # Peer message asks for proof / defends
    assert "chứng minh" in result["message"].lower() or "khác nhau" in result["message"].lower()


def test_peer_pushback_followed_by_ta_hint():
    """After peer has pushed back once, further incomplete attempts go to TA for Socratic hints."""
    orchestrator = MascotOrchestrator()
    orchestrator.start_session()

    # Turn 1: Challenge peer -> Peer pushes back
    res1 = orchestrator.process_turn("Bảo ơi, cậu nhầm rồi đó.")
    assert res1["role"] == Role.PEER.value
    assert orchestrator.peer_pushback_count == 1

    # Turn 2: Still incomplete attempt without proof -> TA steps in with Hint 1
    res2 = orchestrator.process_turn("Thì rõ ràng là khác nhau mà!")
    assert res2["role"] == Role.TA.value
    assert "Gợi ý 1/2" in res2["message"]
    assert orchestrator.hint_count == 1


def test_peer_pushback_followed_by_successful_repair():
    """Learner successfully provides technical proof after peer pushback."""
    orchestrator = MascotOrchestrator()
    orchestrator.start_session()

    # Turn 1: Pushback
    res1 = orchestrator.process_turn("Không phải đâu, cậu nhầm rồi.")
    assert res1["role"] == Role.PEER.value

    # Turn 2: Provide full technical proof
    res2 = orchestrator.process_turn(
        "Nạp chồng (Overloading) trong cùng một lớp khác tham số, "
        "còn ghi đè (Overriding) là trong quan hệ kế thừa lớp cha con cùng tham số!"
    )
    assert res2["role"] == Role.PEER.value
    assert orchestrator.misconception_repaired is True
    assert "hiểu nhầm" in res2["message"].lower() or "cảm ơn" in res2["message"].lower()


def test_peer_pushback_with_mocked_llm():
    """PeerAgent uses LLM for natural pushback when provider is active."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.get_provider.return_value = "mock_groq"
    mock_llm.generate.return_value = "Ủa sao cậu bảo tớ sai? Tớ thấy code chạy y chang nhau mà, cậu giải thích xem!"

    peer = PeerAgent(name="Bảo", initial_misconception="Overloading giống Overriding", llm_client=mock_llm)
    reply = peer.pushback(learner_input="Cậu sai rồi Bảo ơi", concept_title="Đa hình OOP")

    assert "[Bảo]: Ủa sao cậu bảo tớ sai?" in reply
    assert mock_llm.generate.called


def test_ta_explain_back_retry_with_mocked_llm_and_rubric_dimensions():
    """TA uses missing rubric dimensions in LLM Socratic prompt to guide Explain-back."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.get_provider.return_value = "mock_gemini"
    mock_llm.generate.return_value = (
        "Bạn đã nêu đúng quan hệ kế thừa của Overriding! "
        "Nhưng đối với danh sách tham số (Method Signature), hai cơ chế này khác nhau ra sao?"
    )

    ta = TeachingAssistantAgent(name="Thầy Hùng (Trợ giảng)", llm_client=mock_llm)
    reply = ta.prompt_explain_back_retry(
        learner_input="Nạp chồng trong cùng lớp, ghi đè trong kế thừa",
        rubric_feedback="Chưa làm rõ chữ ký hàm",
        missing_dimensions=["method_signature", "polymorphism_type"],
        concept_title="Đa hình OOP",
    )

    assert "[Thầy Hùng (Trợ giảng)]:" in reply
    assert "chữ ký hàm" in reply.lower() or "method signature" in reply.lower()
    assert mock_llm.generate.called

    # Verify that missing_dimensions were passed into system instruction
    _, kwargs = mock_llm.generate.call_args
    assert "method_signature" in kwargs["system_instruction"]


def test_summary_tracks_peer_pushbacks():
    """InstructorSummary records peer_pushback_count accurately."""
    orchestrator = MascotOrchestrator()
    orchestrator.start_session()

    orchestrator.process_turn("Bảo ơi cậu sai rồi")
    summary = orchestrator.generate_instructor_summary()
    assert summary.peer_pushback_count == 1
