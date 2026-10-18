"""Curriculum-gated semantic retrieval adapter for MASCOT lesson content.

Combines TF-IDF vector space modeling with cosine similarity and strict
curriculum scoping (AC1 Grounding, AC2 Future-content denial, Prerequisite policy).
"""

from __future__ import annotations

import collections
import json
import math
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

from mascot.models import Citation, LessonChunk, RetrievalDecision


class SemanticVectorIndex:
    """TF-IDF vector space model with sublinear TF scaling and cosine similarity."""

    def __init__(self, chunks: List[LessonChunk]):
        self.chunks = chunks
        self.doc_count = len(chunks)
        self.df: Dict[str, int] = collections.defaultdict(int)
        self.doc_vectors: List[Dict[str, float]] = []
        self._build_index()

    def tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [w for w in cleaned.split() if len(w) > 1]
        bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def _build_index(self) -> None:
        doc_tokens_list = [self.tokenize(c.text) for c in self.chunks]
        for tokens in doc_tokens_list:
            unique_terms = set(tokens)
            for t in unique_terms:
                self.df[t] += 1

        self.idf: Dict[str, float] = {}
        for t, count in self.df.items():
            self.idf[t] = math.log((1.0 + self.doc_count) / (1.0 + count)) + 1.0

        for tokens in doc_tokens_list:
            vec = self.vectorize(tokens)
            self.doc_vectors.append(vec)

    def vectorize(self, tokens: List[str]) -> Dict[str, float]:
        tf: Dict[str, float] = collections.defaultdict(float)
        for t in tokens:
            tf[t] += 1.0

        vec: Dict[str, float] = {}
        norm_sq = 0.0
        for t, count in tf.items():
            if t in self.idf:
                weight = (1.0 + math.log(count)) * self.idf[t]
                vec[t] = weight
                norm_sq += weight * weight

        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        return {t: w / norm for t, w in vec.items()}

    def score_query(self, query: str, candidate_indices: List[int]) -> List[Tuple[float, int]]:
        tokens = self.tokenize(query)
        q_vec = self.vectorize(tokens)
        if not q_vec:
            return [(0.0, idx) for idx in candidate_indices]

        scores: List[Tuple[float, int]] = []
        for idx in candidate_indices:
            d_vec = self.doc_vectors[idx]
            sim = sum(w * d_vec.get(t, 0.0) for t, w in q_vec.items())
            scores.append((sim, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        return scores


class CurriculumRetriever:
    """Enforces curriculum scope rules and returns citation-bearing chunks using Semantic RAG."""

    def __init__(self, corpus_path: Optional[Path] = None):
        if corpus_path is None:
            corpus_path = Path(__file__).resolve().parent.parent.parent / "data" / "corpus.json"

        self.corpus_path = Path(corpus_path)
        self.chunks: List[LessonChunk] = []
        self.lessons_meta: List[Dict] = []
        self._load_corpus()
        self.vector_index = SemanticVectorIndex(self.chunks)

    def _load_corpus(self) -> None:
        if not self.corpus_path.exists():
            raise FileNotFoundError(f"Corpus file not found at: {self.corpus_path}")

        with open(self.corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        course_id = data.get("course_id", "")
        self.lessons_meta = data.get("lessons", [])
        for lesson in self.lessons_meta:
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
        - Future chunks (lesson_order > current_lesson_order) are strictly denied with zero leakage.
        """
        query_clean = query.strip()
        query_lower = query_clean.lower()

        # 1. Check for Future Content Gating (AC2)
        future_keywords = [
            "abstract", "interface", "trừu tượng", "giao diện", "bài 3", "lesson 3",
            "heap", "malloc", "free", "cấp phát động", "bài 4", "yield", "generator"
        ]
        has_future_keyword = any(kw in query_lower for kw in future_keywords)

        future_indices = [i for i, c in enumerate(self.chunks) if c.lesson_order > current_lesson_order]
        future_scores = self.vector_index.score_query(query_clean, future_indices) if future_indices else []
        top_future_score = future_scores[0][0] if future_scores else 0.0

        if (has_future_keyword or top_future_score > 0.35) and current_lesson_order < 3:
            future_lesson_title = "Bài 3: Lớp trừu tượng & Interface"
            for lesson in self.lessons_meta:
                if lesson.get("lesson_order", 0) > current_lesson_order:
                    future_lesson_title = lesson.get("lesson_title", future_lesson_title)
                    break

            return RetrievalDecision(
                is_authorized=False,
                status="denied_future_content",
                reason=f"Nội dung thuộc bài học tương lai ({future_lesson_title}). Chưa được phép truy xuất trong bài học hiện tại.",
                citations=[],
                chunks=[],
            )

        # 2. Filter Candidate Indices by Curriculum Gate (lesson_order <= current_lesson_order)
        if concept_id:
            candidate_indices = [
                i for i, c in enumerate(self.chunks)
                if c.lesson_order <= current_lesson_order and (c.concept_id == concept_id or c.concept_id.startswith(concept_id))
            ]
            if not candidate_indices:
                candidate_indices = [i for i, c in enumerate(self.chunks) if c.lesson_order <= current_lesson_order]
        else:
            candidate_indices = [i for i, c in enumerate(self.chunks) if c.lesson_order <= current_lesson_order]

        if not candidate_indices:
            return RetrievalDecision(
                is_authorized=False,
                status="insufficient_evidence",
                reason="Không có bài học hợp lệ trong phạm vi chương trình hiện tại.",
                citations=[],
                chunks=[],
            )

        # 3. Vector Space Semantic Ranking
        scored_candidates = self.vector_index.score_query(query_clean, candidate_indices)
        top_scored = [pair for pair in scored_candidates if pair[0] > 0.0]

        top_chunks: List[LessonChunk] = []
        if top_scored:
            top_chunks = [self.chunks[idx] for _, idx in top_scored[:3]]
        elif query_clean:
            # Query has no lexical/semantic overlap, fall back to current lesson overview chunks
            current_lesson_chunks = [c for c in self.chunks if c.lesson_order == current_lesson_order]
            top_chunks = current_lesson_chunks[:2]
        else:
            # Empty query context
            current_lesson_chunks = [c for c in self.chunks if c.lesson_order == current_lesson_order]
            top_chunks = current_lesson_chunks[:2]

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
            reason="Truy xuất thành công tài liệu bài học hiện tại / tiên quyết hợp lệ qua Semantic Vector Index.",
            citations=citations,
            chunks=top_chunks,
        )
