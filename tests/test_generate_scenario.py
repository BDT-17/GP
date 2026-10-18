"""Tests for automated scenario generator."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from mascot.orchestrator import MascotOrchestrator  # noqa: E402
from tools.generate_scenario import (  # noqa: E402
    generate_scenario_from_corpus,
    validate_scenario_schema,
)


def test_validate_scenario_schema() -> None:
    valid_data = {
        "scenario_id": "test_sc",
        "course_id": "CS102",
        "lesson_id": "lesson_1",
        "lesson_order": 1,
        "concept_id": "test_c",
        "concept_title": "Test Concept",
        "peer_student": {
            "name": "Bảo",
            "initial_misconception": "Sai lầm",
        },
        "code_snippet": {
            "code": "print('hello')",
            "simulation_output": "hello",
        },
        "misconception_criteria": {
            "repair_conditions": ["đk1", "đk2"],
        },
        "explain_back_rubric": [
            {"dimension": "dim1", "required_understanding": "req1"},
            {"dimension": "dim2", "required_understanding": "req2"},
        ],
        "escalation_policy": {
            "max_hints_before_escalation": 2,
        },
    }
    assert validate_scenario_schema(valid_data) == []

    # Invalid data missing keys
    invalid = {"scenario_id": "bad"}
    errors = validate_scenario_schema(invalid)
    assert len(errors) > 0


def test_generate_scenario_from_real_corpus(tmp_path: Path) -> None:
    corpus_path = ROOT_DIR / "data" / "courses" / "CS102" / "corpus.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)

    scenario = generate_scenario_from_corpus(corpus_data, lesson_id="lesson_2")
    errors = validate_scenario_schema(scenario)
    assert errors == []
    assert scenario["course_id"] == "CS102"
    assert scenario["lesson_id"] == "lesson_2"
    assert len(scenario["explain_back_rubric"]) >= 2

    # Save to temp file and instantiate Orchestrator with it
    temp_scenario_path = tmp_path / "scenario_gen.json"
    with open(temp_scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, ensure_ascii=False)

    orchestrator = MascotOrchestrator(
        course_id="CS102",
        scenario_path=temp_scenario_path,
        corpus_path=corpus_path,
    )
    initial_msg = orchestrator.start_session()
    assert "Bảo" in orchestrator.peer.name
    assert len(initial_msg) > 10

