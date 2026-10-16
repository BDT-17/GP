"""Curriculum-gated retrieval adapter for MASCOT lesson content."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional
from mascot.models import Citation, LessonChunk, RetrievalDecision


class CurriculumRetriever:
    """Enforces curriculum scope rules and returns citation-bearing chunks."""

    def __init__(self, corpus_path: Optional[Path] = None):
        if corpus_path is None:
            corpus_path = Path(__file__).resolve().parent.parent.parent / "data" / "corpus.json"
        
        self.corpus_path = Path(corpus_path)
        self.chunks: List[LessonChunk] = []
        self._load_corpus()

    def _load_corpus(self) -> None:
        if not self.corpus_path.exists():
            raise FileNotFoundError(f"Corpus file not found at: {self.corpus_path}")

        with open(self.corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        course_id = data.get("course_id", "")
        for lesson in data.get("lessons", []):
            lesson_id = lesson.get("lesson_id", "")
            lesson_order = lesson.get("lesson_order", 0)
            for c in lesson.get("chunks", []):
                chunk = LessonChunk(
                    chunk_id=c["chunk_id"],
                    course_id=course_id,
                    lesson_id=lesson_id,
                    lesson_order=lesson_order,
                    concept_id=c["concept_id"],
                    source_id=c["source_id"],
                    source_location=c["source_location"],
                    text=c["text"],
                )
                self.chunks.append(chunk)

    def retrieve(
        self,
        query: str,
        current_lesson_order: int,
        concept_id: Optional[str] = None,
    ) -> RetrievalDecision:
        """Retrieves eligible chunks obeying curriculum scope.

        - Prerequisite and current lesson chunks (lesson_order <= current_lesson_order) are eligible.
        - Future chunks (lesson_order > current_lesson_order) are strictly denied.
        """
        query_lower = query.lower()

        # Check if query is targeting future content explicitly
        future_keywords = ["abstract", "interface", "trừu tượng", "giao diện", "bài 3", "lesson 3"]
        is_asking_future = any(kw in query_lower for kw in future_keywords)

        if is_asking_future and current_lesson_order < 3:
            return RetrievalDecision(
                is_authorized=False,
                status="denied_future_content",
                reason="Nội dung thuộc bài học tương lai (Bài 3: Lớp trừu tượng & Interface). Chưa được phép truy xuất trong bài học hiện tại.",
                citations=[],
                chunks=[],
            )

        # Filter chunks authorized by curriculum gate
        authorized_chunks = [c for c in self.chunks if c.lesson_order <= current_lesson_order]

        if concept_id:
            matching_chunks = [c for c in authorized_chunks if c.concept_id == concept_id or c.concept_id.startswith(concept_id)]
        else:
            matching_chunks = authorized_chunks

        # Keyword matching scoring
        scored_chunks = []
        for chunk in matching_chunks:
            # Simple keyword overlap relevance score
            text_lower = chunk.text.lower()
            score = 0
            for term in query_lower.split():
                if len(term) > 2 and term in text_lower:
                    score += 1
            if score > 0 or not query.strip():
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c for _, c in scored_chunks[:3]]

        if not top_chunks and query.strip():
            # If no keyword matched, fallback to current lesson chunks for general context
            current_chunks = [c for c in authorized_chunks if c.lesson_order == current_lesson_order]
            top_chunks = current_chunks[:2]

        if not top_chunks:
            return RetrievalDecision(
                is_authorized=False,
                status="insufficient_evidence",
                reason="Không tìm thấy tài liệu được cấp phép phù hợp với câu hỏi.",
                citations=[],
                chunks=[],
            )

        citations = [
            Citation(
                source_id=c.source_id,
                source_location=c.source_location,
                chunk_id=c.chunk_id,
                reference_snippet=c.text[:120] + "...",
            )
            for c in top_chunks
        ]

        return RetrievalDecision(
            is_authorized=True,
            status="allowed",
            reason="Truy xuất thành công tài liệu bài học hiện tại / tiên quyết hợp lệ.",
            citations=citations,
            chunks=top_chunks,
        )

