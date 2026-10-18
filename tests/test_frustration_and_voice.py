"""Tests for learner frustration detection and empathy scaffolding."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from mascot.agents import TeachingAssistantAgent  # noqa: E402
from mascot.orchestrator import MascotOrchestrator  # noqa: E402


def test_ta_detects_frustration_keywords() -> None:
    ta = TeachingAssistantAgent()

    assert ta.detect_frustration("Em chịu rồi khó quá") is True
    assert ta.detect_frustration("Bế tắc quá thầy ơi, em muốn bỏ cuộc") is True
    assert ta.detect_frustration("Chán quá không hiểu gì cả") is True
    assert ta.detect_frustration("Nạp chồng và ghi đè là hai cơ chế khác nhau") is False


def test_ta_hint_delivers_empathy_scaffolding_when_frustrated() -> None:
    ta = TeachingAssistantAgent()
    hint_msg = ta.get_hint(
        hint_level=1,
        learner_input="Em chịu rồi mệt quá không làm được đâu thầy ơi",
        concept_title="Đa hình trong OOP",
    )

    assert "Động viên & Gợi ý" in hint_msg
    assert "Thầy hiểu" in hint_msg
    assert "bối rối" in hint_msg


def test_ta_explain_back_retry_delivers_empathy_when_frustrated() -> None:
    ta = TeachingAssistantAgent()
    feedback_msg = ta.prompt_explain_back_retry(
        learner_input="Khó quá em chịu thôi không biết giải thích thế nào",
        rubric_feedback="Cần nêu rõ phạm vi và chữ ký",
        missing_dimensions=["method_signature"],
        concept_title="Đa hình trong Java",
    )

    assert "Thầy rất hiểu" in feedback_msg
    assert "Cần nêu rõ phạm vi và chữ ký" in feedback_msg


def test_orchestrator_logs_sentiment_event() -> None:
    orchestrator = MascotOrchestrator(course_id="CS102")
    orchestrator.start_session()
    orchestrator.process_turn("Khó quá em chịu rồi thầy ơi")

    sentiment_events = [e for e in orchestrator.event_log if e.event_type == "learner_sentiment"]
    assert len(sentiment_events) == 1
    assert sentiment_events[0].content == "frustrated"

