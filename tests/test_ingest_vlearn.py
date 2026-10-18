"""Tests for VLearn curriculum ingestion tool."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

import pytest  # noqa: E402

from mascot.retriever import CurriculumRetriever  # noqa: E402
from tools.ingest_vlearn import ingest_vlearn_file, parse_slides_text  # noqa: E402


def test_parse_slides_text_with_slide_markers() -> None:
    sample_text = """
--- Slide 1: Giới thiệu đa hình ---
Đa hình là khả năng các đối tượng khác nhau phản ứng khác nhau với cùng một thông điệp.
Phương thức ghi đè (@Override) xảy ra tại thời điểm runtime.

--- Slide 2: Ghi đè phương thức ---
Để ghi đè phương thức hợp lệ trong Java, chữ ký phương thức ở lớp con phải hoàn toàn trùng khớp với lớp cha.
Kiểu trả về phải tương thích covariant.
"""
    result = parse_slides_text(
        content=sample_text,
        course_id="CS102",
        lesson_id="lesson_override",
        lesson_order=2,
        lesson_title="Đa hình trong OOP",
        default_concept_id="polymorphism_overriding",
    )

    assert result["lesson_id"] == "lesson_override"
    assert result["lesson_order"] == 2
    assert result["is_current"] is True
    chunks = result["chunks"]
    assert len(chunks) == 2

    assert chunks[0]["chunk_id"] == "CS102_L2_C1"
    assert chunks[0]["source_location"] == "Slide 1: Giới thiệu đa hình"
    assert "Đa hình là khả năng" in chunks[0]["text"]

    assert chunks[1]["chunk_id"] == "CS102_L2_C2"
    assert chunks[1]["source_location"] == "Slide 2: Ghi đè phương thức"
    assert "chữ ký phương thức ở lớp con" in chunks[1]["text"]


def test_parse_slides_text_fallback_paragraphs() -> None:
    raw_text = """
Đoạn văn thứ nhất nói về khái niệm lập trình hướng đối tượng cơ bản và các tính chất encapsulation, inheritance, polymorphism.

Đoạn văn thứ hai mô tả chi tiết cơ chế con trỏ trong ngôn ngữ lập trình C và sự khác biệt giữa truyền tham trị và truyền tham chiếu.
"""
    result = parse_slides_text(
        content=raw_text,
        course_id="CS101",
        lesson_id="lesson_basics",
        lesson_order=1,
        lesson_title="Nhập môn",
        default_concept_id="intro",
    )

    assert len(result["chunks"]) == 2
    assert "Mục 1, Nhập môn" in result["chunks"][0]["source_location"]
    assert "encapsulation" in result["chunks"][0]["text"]


def test_ingest_vlearn_file_and_merge(tmp_path: Path) -> None:
    lecture_file = tmp_path / "lecture.md"
    lecture_file.write_text(
        "## Slide 1: Pointer Basics\nPointers store memory addresses and dereference with asterisk.\n## Slide 2: Function Pointers\nFunction pointers point to executable code.",
        encoding="utf-8",
    )

    output_corpus = tmp_path / "corpus.json"

    # Step 1: Initial Ingest
    res1 = ingest_vlearn_file(
        file_path=lecture_file,
        course_id="ICT1.002",
        course_name="Lập trình C",
        lesson_id="lesson_ptr",
        lesson_order=1,
        lesson_title="Con trỏ",
        concept_id="pointers",
        output_path=output_corpus,
    )

    assert output_corpus.exists()
    assert len(res1["lessons"]) == 1
    assert len(res1["lessons"][0]["chunks"]) == 2

    # Step 2: Merge a second lesson into existing corpus
    lecture_file_2 = tmp_path / "lecture_2.md"
    lecture_file_2.write_text(
        "--- Slide 1: Dynamic Allocation ---\nmalloc and free manage dynamic memory allocation on heap.",
        encoding="utf-8",
    )

    res2 = ingest_vlearn_file(
        file_path=lecture_file_2,
        course_id="ICT1.002",
        course_name="Lập trình C",
        lesson_id="lesson_heap",
        lesson_order=2,
        lesson_title="Cấp phát động",
        concept_id="heap_memory",
        output_path=output_corpus,
        merge_with_existing=True,
    )

    assert len(res2["lessons"]) == 2
    assert res2["lessons"][0]["lesson_id"] == "lesson_ptr"
    assert res2["lessons"][1]["lesson_id"] == "lesson_heap"

    # Verify integration with CurriculumRetriever loading from output_corpus file
    retriever = CurriculumRetriever(corpus_path=output_corpus)
    decision = retriever.retrieve(
        query="làm sao con trỏ lưu trữ địa chỉ memory address?",
        current_lesson_order=1,
        concept_id="pointers",
    )
    assert decision.is_authorized is True
    assert len(decision.chunks) > 0
    assert any("memory addresses" in c.text for c in decision.chunks)


def test_ingest_missing_file_raises_error() -> None:
    with pytest.raises(FileNotFoundError):
        ingest_vlearn_file(
            file_path="non_existent_file.md",
            course_id="CS102",
            course_name="OOP",
        )

