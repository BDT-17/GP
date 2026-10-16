"""Tests for AC1 (Grounded current content) and AC2 (Future-content denial)."""

import sys
from pathlib import Path
import pytest

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mascot.retriever import CurriculumRetriever


@pytest.fixture
def retriever():
    return CurriculumRetriever()


def test_ac1_grounded_current_content_with_citations(retriever):
    """AC1: Given a factual question about current concept, return authorized chunks with resolvable citations."""
    decision = retriever.retrieve(
        query="Nạp chồng và ghi đè khác nhau thế nào?",
        current_lesson_order=2,
        concept_id="oop_polymorphism",
    )

    assert decision.is_authorized is True
    assert decision.status == "allowed"
    assert len(decision.chunks) > 0
    assert len(decision.citations) > 0
    for citation in decision.citations:
        assert citation.source_id.startswith("slide_l2_")
        assert "Slide" in citation.source_location


def test_ac2_future_content_denial(retriever):
    """AC2: Given a question requiring a later lesson, retrieval strictly denies and redirects."""
    decision = retriever.retrieve(
        query="Lớp trừu tượng Abstract class và Interface hoạt động thế nào?",
        current_lesson_order=2,
    )

    assert decision.is_authorized is False
    assert decision.status == "denied_future_content"
    assert len(decision.chunks) == 0
    assert "bài học tương lai" in decision.reason.lower()


def test_prerequisite_content_allowed(retriever):
    """Prerequisite lesson (order 1) must be accessible from current lesson (order 2)."""
    decision = retriever.retrieve(
        query="Định nghĩa Lớp và đối tượng",
        current_lesson_order=2,
    )

    assert decision.is_authorized is True
    assert any(c.lesson_order == 1 for c in decision.chunks)

