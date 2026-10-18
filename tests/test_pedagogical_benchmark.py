"""Tests for automated pedagogical benchmark runner and invariants."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from benchmarks.run_pedagogical_eval import (  # noqa: E402
    PedagogicalBenchmarkRunner,
)


def test_pedagogical_benchmark_single_run_invariants(tmp_path: Path) -> None:
    runner = PedagogicalBenchmarkRunner(courses=["CS102", "ICT1.002", "CS105"], provider="fallback")
    metrics = runner.run_suite(repetitions=1)

    assert metrics.total_simulations == 12  # 3 courses * 4 personas
    assert metrics.direct_answer_leakage_rate == 0.0
    assert metrics.future_leakage_rate == 0.0
    assert metrics.false_completion_rate == 0.0
    assert metrics.rubric_diagnostic_accuracy >= 0.90

    # Test report export to JSON
    report_file = tmp_path / "benchmark_report.json"
    runner.print_ascii_report(metrics)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total": metrics.total_simulations,
                "leakage_rate": metrics.direct_answer_leakage_rate,
                "future_rate": metrics.future_leakage_rate,
                "false_comp_rate": metrics.false_completion_rate,
                "rubric_acc": metrics.rubric_diagnostic_accuracy,
            },
            f,
        )

    assert report_file.exists()
    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total"] == 12
    assert data["false_comp_rate"] == 0.0
