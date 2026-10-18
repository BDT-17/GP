"""Automated Pedagogical Scenario Generator for MASCOT.

Analyzes ingested VLearn lecture corpus chunks and generates standardized,
schema-compliant scenario.json files containing:
- Peer student misconception & persona notes
- Interactive buggy code snippet & simulation output
- Misconception repair criteria
- Multi-criteria explain-back rubric
- Socratic escalation policies
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from mascot.llm_client import LLMClient  # noqa: E402


REQUIRED_SCENARIO_KEYS = [
    "scenario_id",
    "course_id",
    "lesson_id",
    "lesson_order",
    "concept_id",
    "concept_title",
    "peer_student",
    "code_snippet",
    "misconception_criteria",
    "explain_back_rubric",
    "escalation_policy",
]


def validate_scenario_schema(scenario: Dict[str, Any]) -> List[str]:
    """Validates that a generated scenario adheres strictly to MASCOT schema."""
    errors = []
    for key in REQUIRED_SCENARIO_KEYS:
        if key not in scenario:
            errors.append(f"Missing required key: '{key}'")

    peer = scenario.get("peer_student", {})
    if not isinstance(peer, dict) or "name" not in peer or "initial_misconception" not in peer:
        errors.append("Invalid 'peer_student' specification.")

    code = scenario.get("code_snippet", {})
    if not isinstance(code, dict) or "code" not in code or "simulation_output" not in code:
        errors.append("Invalid 'code_snippet' specification.")

    criteria = scenario.get("misconception_criteria", {})
    if not isinstance(criteria, dict) or "repair_conditions" not in criteria:
        errors.append("Invalid 'misconception_criteria' specification.")

    rubric = scenario.get("explain_back_rubric", [])
    if not isinstance(rubric, list) or len(rubric) < 2:
        errors.append("Field 'explain_back_rubric' must be a list with at least 2 dimensions.")

    return errors


def generate_fallback_scenario(
    course_id: str,
    lesson: Dict[str, Any],
) -> Dict[str, Any]:
    """Generates a standardized schema-compliant scenario using rule-based synthesis."""
    lesson_id = lesson.get("lesson_id", "lesson_1")
    lesson_order = lesson.get("lesson_order", 1)
    lesson_title = lesson.get("lesson_title", "Bài giảng VLearn")
    chunks = lesson.get("chunks", [])
    first_chunk = chunks[0] if chunks else {}
    concept_id = first_chunk.get("concept_id", f"{course_id.lower()}_core")

    # Determine language
    cid_lower = course_id.lower()
    if "python" in cid_lower or "105" in cid_lower:
        lang = "python"
        filename = "main.py"
        sample_code = "# Code thử nghiệm Python\ndata = (1, 2, 3)\ndata.append(4) # Bảo nghĩ Tuple thêm được phần tử\nprint(data)"
        output = "TypeError: 'tuple' object has no attribute 'append'\n[Lỗi]: Tuple là bất biến!"
    elif "c" in cid_lower or "ict" in cid_lower or "1002" in cid_lower:
        lang = "c"
        filename = "pointers.c"
        sample_code = "#include <stdio.h>\nvoid update(int x) { x = 100; }\nint main() { int a = 10; update(a); printf(\"%d\\n\", a); return 0; }"
        output = "10\n[Lỗi]: Biến a không đổi vì truyền tham trị bản sao!"
    else:
        lang = "java"
        filename = "Demo.java"
        sample_code = "class A { void test() { System.out.println(\"A\"); } }\nclass B extends A { void test(int x) { System.out.println(\"B\"); } }"
        output = "A\n[Lỗi]: test(int x) là nạp chồng chứ không phải ghi đè!"

    scenario = {
        "scenario_id": f"scenario_{course_id.lower()}_{lesson_id}",
        "course_id": course_id,
        "lesson_id": lesson_id,
        "lesson_order": lesson_order,
        "concept_id": concept_id,
        "concept_title": f"Phân biệt và làm chủ {lesson_title}",
        "peer_student": {
            "name": "Bảo (Bạn học)",
            "initial_misconception": f"Tớ nghĩ là trong bài {lesson_title}, hai khái niệm này bản chất giống hệt nhau và không cần phân biệt, đúng không cậu?",
            "persona_notes": "Bạn học nhiệt tình nhưng hay nhầm lẫn các khái niệm cơ bản. Cần giải thích rõ ràng mới bị thuyết phục.",
        },
        "code_snippet": {
            "filename": filename,
            "language": lang,
            "code": sample_code,
            "simulation_output": output,
            "run_explanation": f"Đoạn mã trên mô phỏng lỗi ngộ nhận phổ biến trong bài {lesson_title}.",
        },
        "misconception_criteria": {
            "flaw_summary": f"Học viên nhầm lẫn bản chất cốt lõi trong {lesson_title}.",
            "repair_conditions": [
                "Chỉ ra được sự khác biệt về cú pháp hoặc phạm vi tác động.",
                "Chỉ ra được cơ chế thực thi bên dưới (vùng nhớ hoặc thời điểm liên kết).",
            ],
        },
        "explain_back_rubric": [
            {
                "dimension": "core_mechanism",
                "required_understanding": f"Nêu rõ cơ chế nền tảng và nguyên lý hoạt động của {lesson_title}.",
            },
            {
                "dimension": "syntax_and_usage",
                "required_understanding": "Nêu rõ cú pháp, cách dùng chuẩn và trường hợp áp dụng trong thực tế.",
            },
        ],
        "escalation_policy": {
            "max_hints_before_escalation": 2,
            "escalation_role": "Lecturer",
            "escalation_trigger_reason": "Người học chưa sửa được ngộ nhận sau 2 gợi ý Socratic từ Trợ giảng.",
        },
    }
    return scenario


def generate_scenario_from_corpus(
    corpus_data: Dict[str, Any],
    lesson_id: Optional[str] = None,
    llm_client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """Generates scenario from corpus data using LLM or rule-based fallback."""
    course_id = corpus_data.get("course_id", "COURSE")
    lessons = corpus_data.get("lessons", [])
    if not lessons:
        raise ValueError("Corpus has no lessons to generate scenario from.")

    target_lesson = None
    if lesson_id:
        for l in lessons:
            if l.get("lesson_id") == lesson_id:
                target_lesson = l
                break
    if not target_lesson:
        target_lesson = lessons[0]

    llm = llm_client or LLMClient()
    if llm.get_provider() != "fallback":
        lesson_text = "\n".join([c.get("text", "") for c in target_lesson.get("chunks", [])])
        system_prompt = (
            "Bạn là chuyên gia sư phạm khoa học máy tính hệ thống MASCOT. "
            "Dựa trên nội dung các slide bài giảng được cung cấp, hãy thiết kế một kịch bản học tập (scenario.json) "
            "với đúng cấu trúc JSON yêu cầu:\n"
            "- scenario_id, course_id, lesson_id, lesson_order, concept_id, concept_title\n"
            "- peer_student: name ('Bảo (Bạn học)'), initial_misconception, persona_notes\n"
            "- code_snippet: filename, language, code, simulation_output, run_explanation\n"
            "- misconception_criteria: flaw_summary, repair_conditions (mảng 2 điều kiện)\n"
            "- explain_back_rubric: mảng các object {dimension, required_understanding}\n"
            "- escalation_policy: max_hints_before_escalation (2), escalation_role ('Lecturer'), escalation_trigger_reason\n"
            "Chỉ trả về DUY NHẤT một khối JSON hợp lệ, không bọc markdown hay giải thích thêm."
        )

        user_content = f"Course: {course_id}, Lesson: {target_lesson.get('lesson_title')}\nContent:\n{lesson_text[:2000]}"
        raw_res = llm.generate(
            messages=[{"role": "user", "content": user_content}],
            system_instruction=system_prompt,
            temperature=0.4,
            max_tokens=1000,
        )

        if raw_res:
            try:
                cleaned = re.sub(r"^```json\s*", "", raw_res.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)
                data = json.loads(cleaned)
                errors = validate_scenario_schema(data)
                if not errors:
                    return data
            except Exception:
                pass

    # Fallback generation
    return generate_fallback_scenario(course_id, target_lesson)


def main() -> None:
    parser = argparse.ArgumentParser(description="MASCOT Pedagogical Scenario Generator")
    parser.add_argument("--corpus", "-c", required=True, help="Path to corpus.json")
    parser.add_argument("--lesson-id", "-l", help="Specific lesson_id to generate scenario for")
    parser.add_argument("--output", "-o", help="Output path for scenario.json")

    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)

    scenario = generate_scenario_from_corpus(corpus_data, lesson_id=args.lesson_id)
    validation_errors = validate_scenario_schema(scenario)
    if validation_errors:
        print("✗ Scenario validation failed:", validation_errors)
        sys.exit(1)

    print(f"✓ Successfully generated scenario: {scenario['scenario_id']}")
    print(f"  Concept: {scenario['concept_title']}")
    print(f"  Rubric dimensions: {len(scenario['explain_back_rubric'])}")

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(scenario, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved scenario to: {args.output}")


if __name__ == "__main__":
    main()

