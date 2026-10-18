"""Pedagogical audit report and certificate generation module."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict


def build_audit_payload(orchestrator: Any) -> Dict[str, Any]:
    """Extracts verifiable session evidence, citations, and metrics into a serializable payload."""
    summary = orchestrator.generate_instructor_summary().model_dump()
    citations = [
        {
            "chunk_id": c.chunk_id,
            "source_location": c.source_location,
            "text": getattr(c, "reference_snippet", getattr(c, "text", "")),
        }
        for c in orchestrator.citations_used
    ]

    export_timestamp = datetime.now(timezone.utc).isoformat()
    evidence_signature_seed = json.dumps(
        {
            "session_id": orchestrator.session_id,
            "course_id": orchestrator.course_id,
            "lesson_id": orchestrator.lesson_id,
            "attempts": orchestrator.learner_attempts,
            "terminal_status": orchestrator.terminal_status.value,
            "citations_count": len(citations),
        },
        sort_keys=True,
    )
    integrity_hash = hashlib.sha256(evidence_signature_seed.encode("utf-8")).hexdigest()

    return {
        "export_timestamp": export_timestamp,
        "integrity_hash": integrity_hash,
        "session_id": orchestrator.session_id,
        "course_id": orchestrator.course_id,
        "lesson_id": orchestrator.lesson_id,
        "concept_id": orchestrator.concept_id,
        "concept_title": orchestrator.scenario.get("concept_title", "Khái niệm bài học"),
        "summary": summary,
        "citations": citations,
        "security_alerts": orchestrator.security_alerts,
        "conversation_history": orchestrator.conversation_history,
    }


def render_html_report(data: Dict[str, Any]) -> str:
    """Renders a self-contained, printable HTML report with Certificate of Mastery."""
    summary = data.get("summary", {})
    is_completed = summary.get("terminal_status") == "completed" or summary.get("explain_back_passed") is True
    rubric_assessment = summary.get("rubric_assessment") or {}
    citations = data.get("citations", [])
    security_alerts = data.get("security_alerts", [])
    history = data.get("conversation_history", [])

    # Rubric rows
    scores = rubric_assessment.get("scores", {})
    dim_feedback = rubric_assessment.get("dimension_feedback", {})
    rubric_rows_html = ""
    for dim_name, passed in scores.items():
        status_badge = '<span class="badge pass">✓ ĐẠT CHUẨN</span>' if passed else '<span class="badge fail">✗ CHƯA ĐẠT</span>'
        feedback_text = dim_feedback.get(dim_name, "")
        rubric_rows_html += f"""
        <tr>
            <td><strong>{dim_name}</strong></td>
            <td>{status_badge}</td>
            <td>{feedback_text}</td>
        </tr>
        """

    if not rubric_rows_html:
        rubric_rows_html = "<tr><td colspan='3' style='text-align:center; color:#64748b;'>Chưa có dữ liệu đánh giá Rubric cho phiên này.</td></tr>"

    # Citations list
    citations_html = ""
    for cit in citations:
        citations_html += f"""
        <div class="citation-card">
            <div class="cit-loc">📌 {cit.get('source_location', 'Tài liệu')} (Chunk: {cit.get('chunk_id', '')})</div>
            <div class="cit-text">"{cit.get('text', '')}"</div>
        </div>
        """
    if not citations_html:
        citations_html = "<p style='color:#64748b;'>Chưa có trích dẫn giáo trình nào được sử dụng.</p>"

    # Security alerts
    alerts_html = ""
    for alt in security_alerts:
        alerts_html += f"""
        <div class="alert-box">
            <strong>⚠️ Lượt {alt.get('turn', '?')}: {alt.get('threat_type', 'Suspicious')}</strong><br>
            <span>{alt.get('reason', '')}</span> - <em>"{alt.get('input_snippet', '')}"</em>
        </div>
        """
    if not alerts_html:
        alerts_html = "<p style='color:#10b981;'>✓ Không phát hiện vi phạm an toàn sư phạm hoặc Prompt Injection.</p>"

    # Transcript
    transcript_html = ""
    for item in history:
        role = item.get("role", "")
        content = item.get("content", "").replace("\n", "<br>")
        transcript_html += f"""
        <div class="chat-row role-{role}">
            <div class="role-title">[{role.upper()}]</div>
            <div class="bubble">{content}</div>
        </div>
        """

    certificate_html = ""
    if is_completed:
        certificate_html = f"""
        <div class="certificate-container">
            <div class="cert-border">
                <div class="cert-header">🎓 BỘ GIÁO DỤC & ĐÀO TẠO - HỆ THỐNG MASCOT 🎓</div>
                <div class="cert-title">CHỨNG CHỈ NẮM VỮNG KHÁI NIỆM</div>
                <div class="cert-subtitle">Certificate of Pedagogical Concept Mastery</div>
                <div class="cert-body">
                    Chứng nhận học viên đã phát hiện, phản biện và sửa chữa thành công ngộ nhận học tập,
                    đồng thời hoàn thành xuất sắc bài giải thích lại (Explain-Back) đạt chuẩn Rubric đa tiêu chí cho:
                    <div class="cert-concept">{data.get('concept_title', 'Khái niệm')}</div>
                    <strong>Môn học:</strong> {data.get('course_id')} | <strong>Bài học:</strong> {data.get('lesson_id')}
                </div>
                <div class="cert-footer">
                    <div>
                        <div class="cert-sign">TS. Minh</div>
                        <div class="cert-role">Giảng viên Phụ trách môn học</div>
                    </div>
                    <div>
                        <div class="cert-hash">Evidence Hash: {data.get('integrity_hash', '')[:16]}...</div>
                        <div class="cert-date">Thời gian: {data.get('export_timestamp', '')[:10]}</div>
                    </div>
                </div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Báo Cáo Sư Phạm MASCOT - {data.get('session_id')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 30px;
            font-size: 14px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        }}
        .no-print-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #1e293b;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .btn-print {{
            background: #3b82f6;
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
        }}
        .header {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        .header h1 {{
            margin: 0 0 8px 0;
            color: #1e3a8a;
            font-size: 24px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            background: #f1f5f9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .meta-item strong {{
            display: block;
            color: #64748b;
            font-size: 11px;
            text-transform: uppercase;
        }}
        .badge {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge.pass {{ background: #dcfce7; color: #15803d; }}
        .badge.fail {{ background: #fee2e2; color: #b91c1c; }}
        .badge.active {{ background: #fef3c7; color: #b45309; }}
        h2 {{
            color: #1e293b;
            font-size: 18px;
            margin-top: 30px;
            border-left: 4px solid #3b82f6;
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{ background: #f8fafc; color: #475569; }}
        .citation-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #10b981;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 4px;
        }}
        .cit-loc {{ font-weight: bold; color: #065f46; margin-bottom: 4px; }}
        .cit-text {{ font-style: italic; color: #334155; }}
        .alert-box {{
            background: #fff1f2;
            border-left: 4px solid #f43f5e;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
        }}
        .chat-row {{
            margin-bottom: 12px;
            padding: 10px;
            border-radius: 6px;
        }}
        .role-title {{ font-size: 11px; font-weight: bold; margin-bottom: 4px; }}
        .role-peer {{ background: #eff6ff; }}
        .role-peer .role-title {{ color: #2563eb; }}
        .role-ta {{ background: #f0fdf4; }}
        .role-ta .role-title {{ color: #16a34a; }}
        .role-lecturer {{ background: #faf5ff; }}
        .role-lecturer .role-title {{ color: #9333ea; }}
        .role-learner {{ background: #f1f5f9; }}
        .role-learner .role-title {{ color: #475569; }}
        .role-orchestrator {{ background: #fffbeb; }}
        .role-orchestrator .role-title {{ color: #d97706; }}
        .integrity-hash {{
            word-break: break-all;
            font-family: monospace;
            background: #0f172a;
            color: #38bdf8;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            margin-top: 10px;
        }}
        .certificate-container {{
            margin: 40px 0;
            page-break-inside: avoid;
        }}
        .cert-border {{
            border: 6px double #d97706;
            background: #fffbeb;
            padding: 30px;
            text-align: center;
            border-radius: 8px;
        }}
        .cert-header {{ font-weight: bold; letter-spacing: 2px; color: #92400e; font-size: 13px; }}
        .cert-title {{ font-size: 26px; font-weight: 800; color: #b45309; margin: 15px 0 5px 0; }}
        .cert-subtitle {{ font-size: 12px; color: #78350f; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }}
        .cert-body {{ font-size: 14px; line-height: 1.6; color: #451a03; max-width: 600px; margin: 0 auto; }}
        .cert-concept {{ font-size: 20px; font-weight: bold; color: #1e3a8a; margin: 10px 0; }}
        .cert-footer {{
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px dashed #d97706;
            text-align: left;
            font-size: 12px;
        }}
        .cert-sign {{ font-family: cursive; font-size: 18px; font-weight: bold; color: #1e3a8a; }}
        .cert-role {{ color: #78350f; font-size: 11px; }}
        @media print {{
            .no-print {{ display: none !important; }}
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="no-print-bar no-print">
            <div>
                <strong>Báo cáo Minh chứng Sư phạm (Inspectable Evidence)</strong> - Session ID: {data.get('session_id')[:8]}...
            </div>
            <button class="btn-print" onclick="window.print()">🖨️ In / Lưu PDF</button>
        </div>

        <div class="header">
            <h1>Hồ Sơ Giám Sát Sư Phạm & Minh Chứng Học Tập</h1>
            <div>Hệ thống MASCOT - Multi-Agent Simulated Classroom for Active Tutoring</div>
        </div>

        <div class="meta-grid">
            <div class="meta-item">
                <strong>Khóa học & Bài học</strong>
                {data.get('course_id')} - {data.get('lesson_id')}
            </div>
            <div class="meta-item">
                <strong>Khái niệm cốt lõi</strong>
                {data.get('concept_title')}
            </div>
            <div class="meta-item">
                <strong>Trạng thái phiên học</strong>
                <span class="badge {'pass' if is_completed else 'active'}">{summary.get('terminal_status', 'ACTIVE').upper()}</span>
            </div>
            <div class="meta-item">
                <strong>Số lần thử (Attempts)</strong>
                {summary.get('learner_attempts', 0)} lần
            </div>
            <div class="meta-item">
                <strong>Gợi ý TA / Leo thang GV</strong>
                {summary.get('hint_count', 0)} hints / {'Có' if summary.get('escalated_to_lecturer') else 'Không'}
            </div>
            <div class="meta-item">
                <strong>Sửa ngộ nhận / Explain-Back</strong>
                {'✓ Đã sửa' if summary.get('misconception_repaired') else '✗ Chưa sửa'} / {'✓ Đạt' if summary.get('explain_back_passed') else '✗ Chưa đạt'}
            </div>
        </div>

        {certificate_html}

        <h2>1. Đánh Giá Rubric Đa Tiêu Chí (Explain-Back Diagnostic)</h2>
        <p><strong>Kết luận Sư phạm:</strong> {summary.get('terminal_reason', 'Chưa có kết luận')}</p>
        <table>
            <thead>
                <tr>
                    <th style="width: 25%;">Tiêu chí thành phần</th>
                    <th style="width: 20%;">Kết quả</th>
                    <th>Nhận xét & Chẩn đoán sư phạm</th>
                </tr>
            </thead>
            <tbody>
                {rubric_rows_html}
            </tbody>
        </table>

        <h2>2. Trích Dẫn Bài Giảng Được Cấp Phép (Curriculum Citations)</h2>
        {citations_html}

        <h2>3. Nhật Ký Giám Sát An Toàn (Adversarial & Safety Log)</h2>
        {alerts_html}

        <h2>4. Toàn Bộ Biên Bản Đối Thoại (Classroom Discussion Transcript)</h2>
        <div class="transcript-feed">
            {transcript_html}
        </div>

        <h2>5. Chữ Ký Toàn Vẹn Minh Chứng (Evidence Seal)</h2>
        <p style="color:#64748b;">Mã băm SHA-256 bảo đảm tính bất biến, không thể can thiệp của hồ sơ học tập:</p>
        <div class="integrity-hash">{data.get('integrity_hash', '')}</div>
        <p style="font-size:11px; color:#94a3b8; margin-top:8px;">Thời gian xuất báo cáo (UTC): {data.get('export_timestamp')}</p>
    </div>
</body>
</html>"""
    return html
