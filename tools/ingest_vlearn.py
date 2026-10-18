"""VLearn Curriculum Ingestion Tool.

Parses lecture materials (Markdown/Text slides), extracts structured pedagogical chunks
with lesson_order, concept_id, and exact source_location citations, and outputs
standardized corpus.json for Semantic Vector RAG and Curriculum Gating.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional


def parse_slides_text(
    content: str,
    course_id: str,
    lesson_id: str = "lesson_1",
    lesson_order: int = 1,
    lesson_title: str = "Bài giảng VLearn",
    default_concept_id: str = "general_concept",
) -> Dict[str, Any]:
    """Parses raw slide/lecture markdown text into standardized lesson chunks.

    Recognizes slide boundaries formatted as:
    - `--- Slide <N>: <Title> ---`
    - `--- Slide <N> ---`
    - `# Slide <N>: <Title>`
    - `## Slide <N>: <Title>`
    """
    slide_pattern = re.compile(
        r"(?:^|\n)(?:---+\s*Slide\s*(\d+)[:\s]*(.*?)\s*---+|#{1,3}\s*Slide\s*(\d+)[:\s]*(.*?)(?=\n|$))",
        re.IGNORECASE,
    )

    matches = list(slide_pattern.finditer(content))
    chunks: List[Dict[str, Any]] = []

    if not matches:
        # If no slide headers found, treat paragraphs or sections as chunks
        sections = [s.strip() for s in content.split("\n\n") if len(s.strip()) > 30]
        for idx, sec in enumerate(sections, 1):
            chunk_id = f"{course_id}_L{lesson_order}_C{idx}"
            chunks.append({
                "chunk_id": chunk_id,
                "concept_id": default_concept_id,
                "source_id": f"sec_l{lesson_order}_{idx:02d}",
                "source_location": f"Mục {idx}, {lesson_title}",
                "text": sec,
            })
    else:
        for i, match in enumerate(matches):
            slide_num_str = match.group(1) or match.group(3) or str(i + 1)
            slide_title = (match.group(2) or match.group(4) or f"Nội dung {slide_num_str}").strip()
            slide_num = int(slide_num_str) if slide_num_str.isdigit() else (i + 1)

            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start_pos:end_pos].strip()

            if not body:
                body = slide_title

            chunk_id = f"{course_id}_L{lesson_order}_C{i + 1}"
            source_loc = f"Slide {slide_num}: {slide_title}" if slide_title else f"Slide {slide_num}"

            chunks.append({
                "chunk_id": chunk_id,
                "concept_id": default_concept_id,
                "source_id": f"slide_l{lesson_order}_{slide_num:02d}",
                "source_location": source_loc,
                "text": body,
            })

    lesson_data = {
        "lesson_id": lesson_id,
        "lesson_order": lesson_order,
        "lesson_title": lesson_title,
        "is_current": True,
        "chunks": chunks,
    }

    return lesson_data


def ingest_vlearn_file(
    file_path: Path | str,
    course_id: str,
    course_name: str,
    lesson_id: str = "lesson_1",
    lesson_order: int = 1,
    lesson_title: str = "Bài giảng VLearn",
    concept_id: str = "general_concept",
    output_path: Optional[Path | str] = None,
    merge_with_existing: bool = True,
) -> Dict[str, Any]:
    """Ingests a lecture file, builds chunks, and writes or merges into corpus.json."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Lecture file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_lesson = parse_slides_text(
        content=content,
        course_id=course_id,
        lesson_id=lesson_id,
        lesson_order=lesson_order,
        lesson_title=lesson_title,
        default_concept_id=concept_id,
    )

    corpus: Dict[str, Any] = {
        "course_id": course_id,
        "course_name": course_name,
        "lessons": [],
    }

    if output_path:
        out_p = Path(output_path)
        if merge_with_existing and out_p.exists():
            try:
                with open(out_p, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    corpus["course_id"] = existing_data.get("course_id", course_id)
                    corpus["course_name"] = existing_data.get("course_name", course_name)
                    # Filter out duplicate lesson_id if updating
                    corpus["lessons"] = [
                        l for l in existing_data.get("lessons", [])
                        if l.get("lesson_id") != lesson_id
                    ]
            except Exception:
                pass

    # Insert new lesson sorted by lesson_order
    corpus["lessons"].append(new_lesson)
    corpus["lessons"].sort(key=lambda x: x.get("lesson_order", 0))

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(corpus, f, ensure_ascii=False, indent=2)

    return corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="VLearn Curriculum Slide & Lecture Ingestion Tool")
    parser.add_argument("--file", "-f", required=True, help="Path to input lecture file (markdown or txt)")
    parser.add_argument("--course", "-c", required=True, help="Course ID (e.g. CS102, ICT1.002)")
    parser.add_argument("--course-name", "-n", default="Khóa học VLearn", help="Full Course Name")
    parser.add_argument("--lesson-id", default="lesson_1", help="Lesson identifier")
    parser.add_argument("--lesson-order", type=int, default=1, help="Lesson order sequence number")
    parser.add_argument("--lesson-title", default="Bài giảng chính khóa", help="Lesson title")
    parser.add_argument("--concept", default="core_concept", help="Target concept identifier")
    parser.add_argument("--output", "-o", help="Target corpus.json path to write or merge")

    args = parser.parse_args()

    result = ingest_vlearn_file(
        file_path=args.file,
        course_id=args.course,
        course_name=args.course_name,
        lesson_id=args.lesson_id,
        lesson_order=args.lesson_order,
        lesson_title=args.lesson_title,
        concept_id=args.concept,
        output_path=args.output,
    )

    total_chunks = sum(len(l.get("chunks", [])) for l in result.get("lessons", []))
    print(f"✓ Ingested successfully into course {args.course}: {len(result['lessons'])} lesson(s), {total_chunks} chunk(s).")
    if args.output:
        print(f"✓ Output saved to: {args.output}")


if __name__ == "__main__":
    main()

