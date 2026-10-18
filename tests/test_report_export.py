"""Tests for instructor audit report and certificate export."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient  # noqa: E402
import pytest  # noqa: E402

from mascot.orchestrator import MascotOrchestrator  # noqa: E402
from mascot.report_generator import build_audit_payload, render_html_report  # noqa: E402
from server import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_build_audit_payload() -> None:
    orchestrator = MascotOrchestrator(course_id="CS102")
    orchestrator.start_session()
    orchestrator.process_turn("Nạp chồng và ghi đè là hai cơ chế khác nhau.")

    payload = build_audit_payload(orchestrator)

    assert "integrity_hash" in payload
    assert len(payload["integrity_hash"]) == 64  # SHA-256
    assert payload["session_id"] == orchestrator.session_id
    assert payload["course_id"] == "CS102"
    assert "summary" in payload
    assert "conversation_history" in payload
    assert len(payload["conversation_history"]) >= 2


def test_render_html_report_in_progress() -> None:
    orchestrator = MascotOrchestrator(course_id="CS102")
    orchestrator.start_session()

    payload = build_audit_payload(orchestrator)
    html = render_html_report(payload)

    assert "<!DOCTYPE html>" in html
    assert "Hồ Sơ Giám Sát Sư Phạm" in html
    assert payload["integrity_hash"] in html
    assert "window.print()" in html
    # Active session should not display completion certificate
    assert "CHỨNG CHỈ NẮM VỮNG KHÁI NIỆM" not in html


def test_render_html_report_completed_with_certificate() -> None:
    orchestrator = MascotOrchestrator(course_id="CS102")
    orchestrator.start_session()

    # Repair misconception
    orchestrator.process_turn(
        "Bảo ơi cậu nhầm rồi! Nạp chồng xảy ra trong cùng một lớp khác tham số, còn ghi đè xảy ra trong quan hệ kế thừa lớp con ghi đè phương thức lớp cha cùng signature."
    )
    # Complete explain-back
    orchestrator.process_turn(
        "Nạp chồng method overloading xảy ra trong cùng một class với tên hàm giống nhau nhưng khác tham số và quyết định ở compile time. Còn ghi đè method overriding xảy ra khi lớp con kế thừa từ lớp cha với cùng chữ ký phương thức (signature), quyết định liên kết động dynamic binding ở runtime và kiểu trả về có thể covariant."
    )

    assert orchestrator.terminal_status.value == "completed"

    payload = build_audit_payload(orchestrator)
    html = render_html_report(payload)

    assert "CHỨNG CHỈ NẮM VỮNG KHÁI NIỆM" in html
    assert "Certificate of Pedagogical Concept Mastery" in html
    assert "TS. Minh" in html


def test_api_export_report_json(client: TestClient) -> None:
    resp = client.get("/api/instructor/report/export?format=json")
    assert resp.status_code == 200
    data = resp.json()
    assert "integrity_hash" in data
    assert "summary" in data
    assert "citations" in data
    assert "conversation_history" in data
    assert "attachment" in resp.headers.get("content-disposition", "")


def test_api_export_report_html(client: TestClient) -> None:
    resp = client.get("/api/instructor/report/export?format=html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in resp.text
    assert "Hồ Sơ Giám Sát Sư Phạm" in resp.text
