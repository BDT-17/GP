"""Tests for Course and Scenario Modularization (CS102, ICT1.002, CS105)."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import app
from src.mascot.course_manager import CourseManager
from src.mascot.orchestrator import MascotOrchestrator


def test_list_available_courses():
    """Verify CourseManager discovers all registered modular courses."""
    courses = CourseManager.get_available_courses()
    course_ids = [c["course_id"] for c in courses]
    
    assert "CS102" in course_ids
    assert "ICT1.002" in course_ids
    assert "CS105" in course_ids

    # Check ICT1.002 metadata
    ict = next(c for c in courses if c["course_id"] == "ICT1.002")
    assert "Lập trình căn bản" in ict["course_name"]
    assert "prog_param_passing" == ict["concept_id"]


def test_switch_to_basic_programming():
    """Verify switching to Basic Programming (ICT1.002) runs full tutoring lifecycle."""
    orchestrator = MascotOrchestrator()
    init_msg = orchestrator.switch_course("ICT1.002")
    
    assert orchestrator.course_id == "ICT1.002"
    assert orchestrator.concept_id == "prog_param_passing"
    assert "hoanDoi" in init_msg

    # Turn 1: Incorrect attempt
    res1 = orchestrator.process_turn("Tớ cũng nghĩ vậy, đổi a là bên ngoài đổi luôn")
    assert res1["role"] == "ta"
    assert orchestrator.misconception_repaired is False

    # Turn 2: Correct repair attempt
    res2 = orchestrator.process_turn(
        "Không đúng đâu bạn, tham trị chỉ là bản sao chép (copy) nên không đổi biến ngoài, muốn đổi phải dùng tham chiếu hoặc con trỏ"
    )
    assert orchestrator.misconception_repaired is True
    assert "giải thích lại" in res2["message"].lower()

    # Turn 3: Explain-back attempt
    res3 = orchestrator.process_turn(
        "Bản chất tham trị là sao chép giá trị sang ô nhớ mới, hàm gọi không đổi biến gốc bên ngoài; còn tham chiếu truyền địa chỉ ô nhớ bằng ký hiệu & nên mới thay đổi trực tiếp biến gốc."
    )
    assert orchestrator.explain_back_passed is True
    assert orchestrator.terminal_status.value == "completed"
    assert res3["terminal"] is True


def test_switch_to_python():
    """Verify switching to Python (CS105) runs full tutoring lifecycle."""
    orchestrator = MascotOrchestrator()
    init_msg = orchestrator.switch_course("CS105")

    assert orchestrator.course_id == "CS105"
    assert orchestrator.concept_id == "python_list_vs_tuple"
    assert "tuple" in init_msg.lower()

    # Repair attempt
    orchestrator.process_turn(
        "Sai rồi Bảo, list là mutable có thể thay đổi thêm sửa xóa phần tử, còn tuple là immutable bất biến không sửa được"
    )
    assert orchestrator.misconception_repaired is True

    # Explain-back attempt
    res = orchestrator.process_turn(
        "List là kiểu dữ liệu mutable thay đổi được bằng cú pháp [], có hàm append; còn tuple là immutable bất biến với cú pháp (), tối ưu bộ nhớ và an toàn hơn."
    )
    assert orchestrator.explain_back_passed is True
    assert orchestrator.terminal_status.value == "completed"


def test_api_course_endpoints():
    """Verify /api/courses and /api/session/select endpoints."""
    with TestClient(app) as client:
        # 1. Get courses list
        res_list = client.get("/api/courses")
        assert res_list.status_code == 200
        courses = res_list.json()["courses"]
        course_ids = [c["course_id"] for c in courses]
        assert "ICT1.002" in course_ids

        # 2. Select course ICT1.002
        res_select = client.post("/api/session/select", json={"course_id": "ICT1.002"})
        assert res_select.status_code == 200
        data = res_select.json()
        assert data["status"] == "switched"
        assert data["course_id"] == "ICT1.002"
        assert "session_state" in data
        assert data["session_state"]["course_id"] == "ICT1.002"

        # 3. Check /api/session reflects new course and code snippet
        res_session = client.get("/api/session")
        assert res_session.status_code == 200
        assert res_session.json()["course_id"] == "ICT1.002"
        assert "hoandoi.c" in res_session.json()["code_snippet"]["filename"]

        # 4. Run code simulation for switched course
        res_code = client.post("/api/code/run")
        assert res_code.status_code == 200
        code_data = res_code.json()
        assert "hoandoi.c" in code_data["filename"]
        assert "c" in code_data["language"]
        assert len(code_data["code"]) > 0
        assert len(code_data["output"]) > 0


