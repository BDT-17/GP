"""Tests for P3 (Multi-Criteria Rubric Evaluation) and P4 (Semantic Vector RAG & Curriculum Gate)."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root and src are on sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

from mascot.evaluator import Evaluator
from mascot.models import Role, TerminalStatus
from mascot.orchestrator import MascotOrchestrator
from mascot.retriever import CurriculumRetriever, SemanticVectorIndex


def test_semantic_vector_index_ranking():
    """Verify SemanticVectorIndex builds TF-IDF vectors and computes cosine similarity."""
    retriever = CurriculumRetriever()
    assert len(retriever.chunks) > 0

    index = retriever.vector_index
    assert index.doc_count == len(retriever.chunks)
    assert len(index.doc_vectors) == len(retriever.chunks)

    # Search for polymorphism concept
    scores = index.score_query("nạp chồng ghi đè đa hình", list(range(len(retriever.chunks))))
    assert len(scores) == len(retriever.chunks)
    # Top score should be positive and relevant
    assert scores[0][0] > 0.1
    top_chunk = retriever.chunks[scores[0][1]]
    assert "nạp chồng" in top_chunk.text.lower() or "ghi đè" in top_chunk.text.lower() or "đa hình" in top_chunk.text.lower()


def test_semantic_rag_curriculum_gating():
    """Verify semantic retriever enforces strict curriculum gate while utilizing vector similarity."""
    retriever = CurriculumRetriever()

    # 1. Eligible query for current lesson (order 2)
    res_current = retriever.retrieve(
        query="Phương thức nạp chồng overloading trong cùng một lớp",
        current_lesson_order=2,
    )
    assert res_current.is_authorized is True
    assert res_current.status == "allowed"
    assert len(res_current.chunks) > 0
    assert len(res_current.citations) > 0

    # 2. Query targeting future lesson (order 3: Abstract class & Interface)
    res_future = retriever.retrieve(
        query="Lớp trừu tượng abstract class và interface",
        current_lesson_order=2,
    )
    assert res_future.is_authorized is False
    assert res_future.status == "denied_future_content"
    assert len(res_future.chunks) == 0
    assert len(res_future.citations) == 0

    # 3. Prerequisite query (order 1)
    res_prereq = retriever.retrieve(
        query="Định nghĩa về Class và Object",
        current_lesson_order=2,
    )
    assert res_prereq.is_authorized is True
    assert any(c.lesson_order == 1 for c in res_prereq.chunks)


def test_multi_criteria_rubric_partial_attempt():
    """Verify P3: Partial explain-back fails with missing dimensions and diagnostic feedback."""
    orchestrator = MascotOrchestrator()
    evaluator = orchestrator.evaluator

    # Learner only explains scope (same class vs inheritance), missing method signature
    partial_text = "Nạp chồng là trong cùng một lớp, còn ghi đè là trong quan hệ kế thừa giữa lớp cha và con."
    outcome = evaluator.evaluate_explain_back(partial_text)

    assert outcome.explain_back_passed is False
    assert outcome.needs_support is True
    assert outcome.rubric_scores["scope_and_inheritance"] is True
    assert outcome.rubric_scores["method_signature"] is False
    assert "method_signature" in outcome.missing_dimensions
    assert outcome.score_percentage < 100.0
    assert "tham số" in outcome.feedback.lower()


def test_multi_criteria_rubric_complete_attempt():
    """Verify P3: Complete explain-back passes with all mandatory dimensions."""
    orchestrator = MascotOrchestrator()
    evaluator = orchestrator.evaluator

    full_text = (
        "Nạp chồng là các hàm trong cùng một lớp có tên giống nhau nhưng khác danh sách tham số. "
        "Còn ghi đè là phương thức ở lớp con kế thừa từ lớp cha có tên và cùng tham số giống hệt nhau."
    )
    outcome = evaluator.evaluate_explain_back(full_text)

    assert outcome.explain_back_passed is True
    assert outcome.needs_support is False
    assert outcome.rubric_scores["scope_and_inheritance"] is True
    assert outcome.rubric_scores["method_signature"] is True
    assert len(outcome.missing_dimensions) == 0
    assert outcome.score_percentage >= 66.0


def test_orchestrator_ta_diagnostic_feedback():
    """Verify TA returns diagnostic feedback guiding the learner on missing rubric dimensions."""
    orchestrator = MascotOrchestrator()
    orchestrator.start_session()

    # Step 1: Repair misconception
    orchestrator.process_turn("Overloading trong cùng một lớp khác tham số, còn Overriding là kế thừa cùng tham số")
    assert orchestrator.misconception_repaired is True

    # Step 2: Submit incomplete explain-back (missing signature)
    res = orchestrator.process_turn("Nạp chồng là trong cùng một lớp, ghi đè là qua quan hệ kế thừa lớp cha con.")
    assert orchestrator.explain_back_passed is False
    assert res["role"] == Role.TA.value
    # TA reply should contain diagnostic rubric hint
    assert "chữ ký hàm" in res["message"].lower() or "tham số" in res["message"].lower()

    # Verify summary includes rubric assessment
    summary = orchestrator.generate_instructor_summary()
    assert summary.rubric_assessment is not None
    assert "scores" in summary.rubric_assessment
    assert "missing_dimensions" in summary.rubric_assessment
    assert "method_signature" in summary.rubric_assessment["missing_dimensions"]


def test_api_session_exposes_rubric_assessment():
    """Verify /api/session endpoint returns rubric_assessment after explain-back attempt."""
    from server import app
    with TestClient(app) as client:
        client.post("/api/reset")

        # Step 1: Repair
        client.post(
            "/api/chat",
            json={"message": "Overloading trong cùng một lớp khác tham số, còn Overriding là kế thừa cùng tham số"},
        )

        # Step 2: Partial explain-back
        client.post(
            "/api/chat",
            json={"message": "Nạp chồng trong cùng lớp, ghi đè kế thừa cha con"},
        )

        session_res = client.get("/api/session")
        assert session_res.status_code == 200
        data = session_res.json()
        assert "rubric_assessment" in data
        assert data["rubric_assessment"] is not None
        assert "scores" in data["rubric_assessment"]
        assert "score_percentage" in data["rubric_assessment"]
