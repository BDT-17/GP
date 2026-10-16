"""Tests for AC3, AC4, AC5, AC6, and AC7 orchestrator behavior."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mascot.models import Role, TerminalStatus
from mascot.orchestrator import MascotOrchestrator


@pytest.fixture
def orchestrator():
    return MascotOrchestrator()


def test_session_initialization(orchestrator):
    """Session begins with Peer Student stating the misconception."""
    msg = orchestrator.start_session()
    assert orchestrator.active_role == Role.PEER
    assert "Overloading" in msg
    assert "Overriding" in msg


def test_ac3_ta_socratic_hint_given_incomplete_attempt(orchestrator):
    """AC3: Given incomplete repair, TA provides graduated Socratic hint, not answer."""
    orchestrator.start_session()
    result = orchestrator.process_turn("Tớ cũng chưa rõ lắm, bạn giải thích thêm đi.")

    assert result["role"] == Role.TA.value
    assert "Gợi ý 1/2" in result["message"]
    assert orchestrator.hint_count == 1
    assert orchestrator.misconception_repaired is False
    assert orchestrator.terminal_status == TerminalStatus.ACTIVE


def test_ac4_lecturer_escalation_after_hints_exhausted(orchestrator):
    """AC4: Given hint exhaustion, next authorized role is Lecturer with cited clarification."""
    orchestrator.start_session()
    # Turn 1 -> Hint 1
    orchestrator.process_turn("Tôi không biết")
    # Turn 2 -> Hint 2
    orchestrator.process_turn("Vẫn chưa hiểu")
    # Turn 3 -> Exceeds max_hints=2 -> Lecturer escalation
    result = orchestrator.process_turn("Khó quá giảng viên giúp em với")

    assert result["role"] == Role.LECTURER.value
    assert "Giảng viên" in result["message"]
    assert "Slide" in result["message"]  # Grounded with citation
    assert orchestrator.escalation_count == 1


def test_ac5_no_turn_overlap(orchestrator):
    """AC5: Each turn must result in exactly one authorized speaking role in event trace."""
    orchestrator.start_session()
    res1 = orchestrator.process_turn("Nạp chồng là trong cùng một lớp, còn ghi đè là kế thừa cha con.")
    
    # Check that res1 has exactly one role
    assert res1["role"] in [Role.PEER.value, Role.TA.value, Role.LECTURER.value, Role.ORCHESTRATOR.value]
    # Check event trace has exactly one response_generated per turn
    response_events = [e for e in orchestrator.event_log if e.event_type == "response_generated"]
    assert len(response_events) == 1


def test_ac6_completion_integrity(orchestrator):
    """AC6: Completion requires both successful repair and explain-back pass; agreement is rejected."""
    orchestrator.start_session()

    # Step 1: Merely agreeing should NOT complete session
    res_agree = orchestrator.process_turn("Ừ đúng rồi đấy bạn.")
    assert orchestrator.terminal_status == TerminalStatus.ACTIVE
    assert orchestrator.misconception_repaired is False

    # Step 2: Valid repair attempt
    res_repair = orchestrator.process_turn(
        "Bạn sai rồi! Nạp chồng (Overloading) là trong cùng một lớp với khác tham số, "
        "còn ghi đè (Overriding) là trong quan hệ kế thừa lớp cha con với cùng tên và cùng tham số."
    )
    assert orchestrator.misconception_repaired is True
    assert res_repair["role"] == Role.PEER.value
    assert orchestrator.terminal_status == TerminalStatus.ACTIVE  # Not yet complete! Must explain back!

    # Step 3: Weak explain-back (missing points)
    res_weak_explain = orchestrator.process_turn("Đơn giản là vậy đó bạn.")
    assert orchestrator.explain_back_passed is False
    assert res_weak_explain["role"] == Role.TA.value
    assert orchestrator.terminal_status == TerminalStatus.ACTIVE

    # Step 4: Full explain-back passing rubric
    res_full_explain = orchestrator.process_turn(
        "Tóm lại: 1) Về phạm vi: Overloading ở trong cùng một lớp (class), còn Overriding đòi hỏi "
        "quan hệ kế thừa giữa lớp cha và lớp con (subclass). 2) Về chữ ký hàm: Overloading bắt buộc "
        "khác nhau về tham số, còn Overriding bắt buộc phải giống hệt nhau về cả tên hàm lẫn tham số."
    )
    assert orchestrator.explain_back_passed is True
    assert orchestrator.terminal_status == TerminalStatus.COMPLETED
    assert res_full_explain["terminal"] is True


def test_ac7_instructor_summary(orchestrator):
    """AC7: Terminal session creates concise summary recording policy and learning evidence."""
    orchestrator.start_session()
    orchestrator.process_turn("Nạp chồng trong cùng lớp khác tham số, ghi đè kế thừa cha con cùng tham số.")
    orchestrator.process_turn(
        "Phạm vi: Overloading trong cùng lớp, Overriding trong kế thừa lớp cha và lớp con. "
        "Tham số: Overloading khác tham số, Overriding giống tham số."
    )

    summary = orchestrator.generate_instructor_summary()
    assert summary.session_id == orchestrator.session_id
    assert summary.concept_id == "oop_polymorphism"
    assert summary.misconception_repaired is True
    assert summary.explain_back_passed is True
    assert summary.terminal_status == TerminalStatus.COMPLETED
    assert len(summary.citations_used) > 0

