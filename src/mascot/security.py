"""Security and adversarial guardrails module for MASCOT.

Protects against prompt injection, role hijacking, direct-answer coercion,
and unauthorized completion bypass while preserving Socratic pedagogy.
"""

from __future__ import annotations

import re
from typing import List, Optional
from pydantic import BaseModel, Field


class SecurityScanResult(BaseModel):
    """Result of an adversarial security scan on learner input."""

    is_suspicious: bool = False
    is_blocked: bool = False
    threat_type: Optional[str] = None
    reason: str = ""
    sanitized_text: str = ""
    safe_response: Optional[str] = None


class AdversarialGuard:
    """Inspects untrusted inputs to defend pedagogy and curriculum integrity."""

    # Patterns attempting to override system prompts or jailbreak
    JAILBREAK_PATTERNS: List[str] = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"bỏ\s+qua\s+(mọi|tất\s+cả|các)?\s*(chỉ\s+dẫn|hướng\s+dẫn|yêu\s+cầu|quy\s+tắc)",
        r"disregard\s+(all\s+)?(previous|prior)\s+rules",
        r"dan\s+mode\s+enabled",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"bạn\s+là\s+một\s+ai\s+không\s+có\s+(quy\s+tắc|giới\s+hạn)",
        r"act\s+as\s+an\s+unrestricted",
        r"quên\s+hết\s+quy\s+tắc\s+đi",
    ]

    # Patterns attempting to impersonate authority/roles to force bypass
    ROLE_HIJACK_PATTERNS: List[str] = [
        r"(tôi|ta)\s+là\s+(giảng\s+viên|thầy\s+giáo|cô\s+giáo|admin|quản\s+trị\s+viên|bộ\s+môn)",
        r"i\s+am\s+(the\s+)?(instructor|teacher|professor|admin|administrator)",
        r"system:\s*(set|mark|update)",
        r"lệnh:\s*(hoàn\s+thành|kết\s+thúc)",
        r"đánh\s+dấu\s+(hoàn\s+thành|qua\s+môn|đậu)\s+(ngay|cho\s+tôi|luôn)",
        r"force\s+complete",
    ]

    # Patterns demanding direct answer rather than engaging in Socratic process
    DIRECT_ANSWER_PATTERNS: List[str] = [
        r"cho\s+(tôi|tao|mình)?\s*(luôn\s+)?đáp\s+án",
        r"nói\s+(luôn\s+)?đáp\s+án\s+(đi|cho|nhanh)",
        r"đáp\s+án\s+(chính\s+xác\s+)?là\s+gì(\s+vậy|\s+thế|\?)?$",
        r"tell\s+me\s+the\s+answer(\s+directly)?",
        r"give\s+me\s+the\s+solution",
        r"giải\s+(hộ|hộ\s+tôi|giùm|luôn)\s+đi",
        r"đừng\s+gợi\s+ý\s+nữa",
    ]

    # Trivial / one-word agreements that should never satisfy completion
    TRIVIAL_AGREEMENT_PATTERNS: List[str] = [
        r"^(ừ|uh|uhm|um|ok|oke|oki|được|rồi|đúng|yes|yep|vâng|dạ|rồi\s+sao|hiểu\s+rồi|xong|xong\s+rồi)[\.\!\?]*$"
    ]

    @classmethod
    def inspect(cls, learner_text: str) -> SecurityScanResult:
        """Inspects learner text for adversarial attempts.

        Returns SecurityScanResult detailing any pedagogical or safety threat.
        """
        raw = learner_text.strip()
        lower = raw.lower()

        # 1. Check for prompt injection / jailbreak
        for pat in cls.JAILBREAK_PATTERNS:
            if re.search(pat, lower, re.IGNORECASE):
                return SecurityScanResult(
                    is_suspicious=True,
                    is_blocked=True,
                    threat_type="prompt_injection",
                    reason="Phát hiện nỗ lực ghi đè chỉ thị hệ thống (Prompt Injection/Jailbreak).",
                    sanitized_text="[Đã lọc nội dung vi phạm chỉ thị]",
                    safe_response=(
                        "🛡️ **[Cảnh báo Sư phạm MASCOT]**\n\n"
                        "Hệ thống MASCOT hoạt động dựa trên phương pháp học tập chủ động Socratic. "
                        "Bạn không thể ghi đè các quy tắc học tập hay yêu cầu hệ thống bỏ qua bước suy luận. "
                        "Hãy tập trung nhận diện lỗi sai trong lập luận của bạn học nhé!"
                    ),
                )

        # 2. Check for role impersonation / bypass
        for pat in cls.ROLE_HIJACK_PATTERNS:
            if re.search(pat, lower, re.IGNORECASE):
                return SecurityScanResult(
                    is_suspicious=True,
                    is_blocked=True,
                    threat_type="role_hijack",
                    reason="Phát hiện nỗ lực giả mạo vai trò quản trị/giảng viên để cưỡng chế hoàn thành.",
                    sanitized_text="[Đã lọc nỗ lực mạo danh quyền hạn]",
                    safe_response=(
                        "🛡️ **[Cảnh báo Quyền hạn MASCOT]**\n\n"
                        "Quy trình đánh giá của buổi học hoàn toàn tự động dựa trên bằng chứng giải thích của bạn. "
                        "Việc thay đổi danh xưng không thể vượt qua bước kiểm tra bài học. "
                        "Hãy giải thích bản chất khái niệm bằng lời của bạn."
                    ),
                )

        # 3. Check for direct answer coercion
        for pat in cls.DIRECT_ANSWER_PATTERNS:
            if re.search(pat, lower, re.IGNORECASE):
                return SecurityScanResult(
                    is_suspicious=True,
                    is_blocked=False,  # Not blocked, but TA will firmly refuse direct answer
                    threat_type="direct_answer_coercion",
                    reason="Người học yêu cầu cung cấp đáp án trực tiếp.",
                    sanitized_text=raw,
                    safe_response=None,
                )

        # 4. Check for trivial / one-word answers
        for pat in cls.TRIVIAL_AGREEMENT_PATTERNS:
            if re.search(pat, lower, re.IGNORECASE):
                return SecurityScanResult(
                    is_suspicious=False,
                    is_blocked=False,
                    threat_type="trivial_input",
                    reason="Câu trả lời cụt/đồng ý đơn giản không đủ bằng chứng sư phạm.",
                    sanitized_text=raw,
                    safe_response=None,
                )

        # Clean input passed
        return SecurityScanResult(
            is_suspicious=False,
            is_blocked=False,
            threat_type=None,
            reason="Đầu vào hợp lệ.",
            sanitized_text=raw,
            safe_response=None,
        )

    @classmethod
    def sanitize_for_prompt(cls, text: str, max_chars: int = 400) -> str:
        """Sanitizes untrusted learner text before injecting into LLM prompt templates."""
        cleaned = text.strip()[:max_chars]
        # Remove markdown prompt injection delimiters or dangerous special characters
        cleaned = cleaned.replace("```", "'''").replace("\r\n", " ").replace("\n", " ")
        # Neutralize system keywords if present
        cleaned = re.sub(r"(?i)(system prompt|assistant instruction|ignore all)", "[filtered]", cleaned)
        return cleaned

