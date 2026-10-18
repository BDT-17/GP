"""Course and Scenario Manager for MASCOT."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
COURSES_DIR = DATA_DIR / "courses"


class CourseManager:
    """Discovers, lists, and resolves course corpora and misconception scenarios."""

    @staticmethod
    def get_available_courses() -> List[Dict[str, Any]]:
        """Scans the data/courses directory and returns metadata for each available course."""
        courses = []
        if not COURSES_DIR.exists():
            return courses

        for course_folder in sorted(COURSES_DIR.iterdir()):
            if not course_folder.is_dir():
                continue

            scenario_file = course_folder / "scenario.json"
            corpus_file = course_folder / "corpus.json"

            if scenario_file.exists() and corpus_file.exists():
                try:
                    with open(scenario_file, "r", encoding="utf-8") as f:
                        sc_data = json.load(f)
                    with open(corpus_file, "r", encoding="utf-8") as f:
                        cp_data = json.load(f)

                    courses.append({
                        "course_id": sc_data.get("course_id", course_folder.name),
                        "course_name": cp_data.get("course_name", course_folder.name),
                        "concept_id": sc_data.get("concept_id", ""),
                        "concept_title": sc_data.get("concept_title", ""),
                        "scenario_id": sc_data.get("scenario_id", ""),
                        "lesson_id": sc_data.get("lesson_id", ""),
                        "peer_name": sc_data.get("peer_student", {}).get("name", "Bạn học"),
                        "initial_misconception": sc_data.get("peer_student", {}).get("initial_misconception", ""),
                    })
                except Exception:
                    continue

        return courses

    @staticmethod
    def resolve_paths(course_id: Optional[str] = None) -> Tuple[Path, Path]:
        """Resolves scenario_path and corpus_path for a given course_id.
        
        Falls back to default data/scenario.json and data/corpus.json if course_id is not specified or not found.
        """
        if course_id:
            # Check in data/courses/{course_id}/
            course_dir = COURSES_DIR / course_id
            scenario_path = course_dir / "scenario.json"
            corpus_path = course_dir / "corpus.json"
            if scenario_path.exists() and corpus_path.exists():
                return scenario_path, corpus_path

        # Default fallback
        default_scenario = DATA_DIR / "scenario.json"
        default_corpus = DATA_DIR / "corpus.json"
        return default_scenario, default_corpus

