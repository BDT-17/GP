"""Interactive Command-Line Interface (CLI) demo for MASCOT."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mascot.models import Role, TerminalStatus
from mascot.orchestrator import MascotOrchestrator


def run_cli_demo():
    print("=" * 70)
    print("🎓 MASCOT - Lớp học mô phỏng AI (CLI Demo)")
    print("   Chủ đề: Nạp chồng (Overloading) vs Ghi đè (Overriding)")
    print("   Gõ 'exit' hoặc 'quit' để thoát.")
    print("=" * 70)

    orch = MascotOrchestrator()
    initial_msg = orch.start_session()
    print(f"\n{initial_msg}\n")

    while orch.terminal_status == TerminalStatus.ACTIVE:
        try:
            user_input = input("\n[Bạn (Learner)]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát phiên học.")
            break

        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("Kết thúc phiên học trước hạn.")
            break

        result = orch.process_turn(user_input)
        role = result["role"]
        message = result["message"]

        print(f"\n{message}\n")

        if result.get("terminal"):
            print("=" * 70)
            print("📊 TỔNG KẾT PHIÊN HỌC CHO GIẢNG VIÊN:")
            summary = orch.generate_instructor_summary()
            print(json.dumps(summary.model_dump(), indent=2, ensure_ascii=False))
            print("=" * 70)
            break


if __name__ == "__main__":
    run_cli_demo()

