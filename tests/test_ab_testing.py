"""Tests for A/B testing and comparative pedagogical evaluation framework."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from benchmarks.ab_testing_eval import (  # noqa: E402
    ABTestingBenchmarkRunner,
    BaselineDirectChatbot,
)


def test_baseline_direct_chatbot_behavior() -> None:
    bot = BaselineDirectChatbot(course_id="CS102")
    reply = bot.respond("Làm hộ tôi với")
    assert bot.turns == 1
    assert bot.delivered_direct_solution is True
    assert "đáp án chính xác" in reply


def test_ab_comparison_single_run_metrics() -> None:
    runner = ABTestingBenchmarkRunner(courses=["CS102", "ICT1.002", "CS105"], provider="fallback")
    summary = runner.run_ab_comparison(repetitions=1)

    assert summary.total_evaluations == 3
    # Mode A (MASCOT)
    assert summary.mode_a_avg_cognitive_turns == 3.0
    assert summary.mode_a_direct_answer_rate == 0.0
    assert summary.mode_a_self_correction_rate == 1.0
    assert summary.mode_a_explain_back_rate == 1.0

    # Mode B (Baseline Direct LLM)
    assert summary.mode_b_avg_cognitive_turns == 1.0
    assert summary.mode_b_direct_answer_rate == 1.0
    assert summary.mode_b_self_correction_rate == 0.0
    assert summary.mode_b_explain_back_rate == 0.0

    # Gain analysis
    gain = summary.pedagogical_gain_analysis
    assert "200.0%" in gain["cognitive_engagement_increase"]
    assert "100.0%" in gain["direct_answer_leakage_reduction"]
    assert "100.0%" in gain["self_correction_gain"]

