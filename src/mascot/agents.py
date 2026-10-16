"""Role definitions and response adapters for Peer, TA, and Lecturer."""

from __future__ import annotations

from typing import Dict, List, Optional
from mascot.models import Citation, Role


class PeerAgent:
    """Simulates a classmate expressing misconceptions and receiving peer tutoring."""

    def __init__(self, name: str, initial_misconception: str):
        self.name = name
        self.initial_misconception = initial_misconception

    def get_initial_statement(self) -> str:
        return self.initial_misconception

    def acknowledge_repair(self) -> str:
        return (
            f"[{self.name}]: À, hóa ra tớ đã hiểu nhầm giữa nạp chồng và ghi đè! "
            "Cậu nói rất có lý. Nhưng để tớ chắc chắn không quên, cậu có thể giải thích "
            "tổng kết lại bằng lời của cậu xem 2 khái niệm này khác nhau ở những điểm cốt lõi nào không?"
        )

    def ask_for_clarification(self) -> str:
        return (
            f"[{self.name}]: Tớ vẫn hơi lấn cấn... Ý cậu là hai cái này khác nhau ở chỗ nào cụ thể vậy?"
        )


class TeachingAssistantAgent:
    """Socratic TA offering graduated hints without providing direct answers (AC3)."""

    def __init__(self, name: str = "Thầy Hùng (Trợ giảng)"):
        self.name = name
        self.hints = [
            (
                f"[{self.name} - Gợi ý 1/2]: Hãy chú ý đến phạm vi xuất hiện của chúng. "
                "Liệu hai phương thức nạp chồng (Overloading) có thể nằm trong cùng một class không? "
                "Còn ghi đè (Overriding) thì có đòi hỏi mối quan hệ giữa lớp cha và lớp con không?"
            ),
            (
                f"[{self.name} - Gợi ý 2/2]: Rất gần rồi! Giờ bạn hãy nhìn vào chữ ký hàm (Method Signature) và danh sách tham số. "
                "Để nạp chồng được thì tham số bắt buộc phải như thế nào? Và khi lớp con ghi đè thì tham số có được phép thay đổi không?"
            ),
        ]

    def get_hint(self, hint_level: int) -> str:
        """Returns graduated hint based on hint counter."""
        idx = min(max(0, hint_level - 1), len(self.hints) - 1)
        return self.hints[idx]

    def prompt_explain_back_retry(self) -> str:
        return (
            f"[{self.name}]: Bạn đã đi đúng hướng rồi! Tuy nhiên phần giải thích lại (Explain-back) "
            "cần nêu rõ cả 2 khía cạnh: (1) Phạm vi lớp & Kế thừa và (2) Sự giống/khác nhau về tham số. "
            "Bạn hãy thử trình bày lại một lần nữa nhé!"
        )


class LecturerAgent:
    """Provides authoritative, grounded clarification upon escalation (AC4)."""

    def __init__(self, name: str = "TS. Minh (Giảng viên)"):
        self.name = name

    def provide_clarification(self, citations: List[Citation]) -> str:
        citation_str = "\n".join([f"  • {c.source_location}: {c.reference_snippet}" for c in citations])
        return (
            f"[{self.name} - Giảng viên hỗ trợ chuyên sâu]:\n"
            "Chào các bạn, tôi nhận thấy các bạn đang gặp khó khăn trong việc phân biệt Nạp chồng và Ghi đè. "
            "Tôi xin giải thích ngắn gọn dựa trên bài giảng chính thức:\n\n"
            "1. **Method Overloading (Nạp chồng)**: Diễn ra TRONG CÙNG 1 LỚP. Tên hàm giống nhau nhưng BẮT BUỘC KHÁC DANH SÁCH THAM SỐ (số lượng/kiểu/thứ tự). Đây là đa hình lúc biên dịch (Compile-time).\n"
            "2. **Method Overriding (Ghi đè)**: Diễn ra giữa LỚP CON VÀ LỚP CHA (quan hệ kế thừa). Lớp con viết lại hàm của lớp cha với TÊN VÀ THAM SỐ GIỐNG HỆT. Đây là đa hình lúc chạy (Runtime).\n\n"
            f"📚 **Trích dẫn tài liệu tham khảo:**\n{citation_str}\n\n"
            "Bây giờ, bạn hãy vận dụng kiến thức này để hoàn thành phần giải thích lại (Explain-back) của mình nhé!"
        )

