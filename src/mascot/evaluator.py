"""Evaluator module for assessing misconception repair and explain-back against rubric."""

from __future__ import annotations

import re
from typing import Dict, Tuple
from mascot.models import EvaluationOutcome


class Evaluator:
    """Evaluates learner inputs against misconception criteria and explain-back rubric."""

    def __init__(self, scenario_data: Dict):
        self.scenario = scenario_data
        self.rubric = scenario_data.get("explain_back_rubric", [])

    def evaluate_repair_attempt(self, user_text: str) -> Tuple[bool, bool, str]:
        """Assesses if user successfully pointed out the flaw in the Peer's misconception.

        Returns:
            (repaired: bool, needs_help: bool, feedback: str)
        """
        text = user_text.lower()

        # Check if user is asking for help or is stuck
        help_patterns = [
            "gợi ý", "chịu", "không biết", "giúp", "bế tắc", "đáp án là gì",
            "cho đáp án", "nói luôn đi", "hint", "help"
        ]
        needs_help = any(p in text for p in help_patterns)

        # Check for key distinguishing dimensions of Overloading vs Overriding
        mentions_same_class = any(p in text for p in ["cùng lớp", "cùng một lớp", "trong 1 lớp", "cùng class", "same class"])
        mentions_diff_params = any(p in text for p in ["khác tham số", "khác kiểu", "số lượng tham số", "khác signature", "khác nhau về tham số", "different parameter"])
        
        mentions_inheritance = any(p in text for p in ["kế thừa", "lớp cha", "lớp con", "cha con", "subclass", "superclass", "extends", "inheritance"])
        mentions_same_signature = any(p in text for p in ["cùng tham số", "giống hệt", "giống tham số", "cùng tên và tham số", "same signature", "ghi đè lại"])

        # Sufficient repair condition: mentions at least distinction in scope or parameters
        has_overloading_point = mentions_same_class or mentions_diff_params
        has_overriding_point = mentions_inheritance or mentions_same_signature

        if has_overloading_point and has_overriding_point:
            return True, False, "Người học đã chỉ ra thành công điểm khác biệt cốt lõi giữa Overloading và Overriding."
        elif has_overloading_point or has_overriding_point:
            # Partially correct, needs one more push
            return False, needs_help, "Người học đã nhận diện được một phần, nhưng cần làm rõ thêm khía cạnh còn lại."
        else:
            return False, needs_help, "Người học chưa chỉ ra được lỗi sai trong phát biểu của bạn học."

    def evaluate_explain_back(self, user_text: str) -> EvaluationOutcome:
        """Assesses learner's self-generated explain-back against the 3-point rubric (AC6)."""
        text = user_text.lower()

        # Rubric Dim 1: Scope & Inheritance
        has_same_class = ("cùng" in text or "trong" in text or "same" in text) and ("lớp" in text or "class" in text)
        has_inheritance = any(p in text for p in ["kế thừa", "lớp cha", "lớp con", "cha con", "subclass", "superclass", "extends", "inheritance"])
        has_scope = has_same_class and has_inheritance

        # Rubric Dim 2: Method Signature & Parameters
        has_diff_params = ("khác" in text or "different" in text) and ("tham số" in text or "parameter" in text or "signature" in text)
        has_same_params = ("cùng" in text or "giống" in text or "same" in text or "hệt" in text) and ("tham số" in text or "parameter" in text or "signature" in text or "tên" in text)
        has_signature = has_diff_params and has_same_params

        # Rubric Dim 3: Compile-time vs Runtime (Bonus point)
        has_polymorphism_type = any(p in text for p in ["biên dịch", "compile", "thực thi", "runtime", "tĩnh", "động"])

        rubric_scores = {
            "scope_and_inheritance": has_scope,
            "method_signature": has_signature,
            "polymorphism_type": has_polymorphism_type,
        }

        # Passing requires at least Dim 1 and Dim 2
        is_pass = has_scope and has_signature

        feedback = (
            "Giải thích xuất sắc và đầy đủ bản chất!"
            if is_pass
            else "Bài giải thích còn thiếu khía cạnh phạm vi lớp hoặc tính chất của tham số. Hãy bổ sung đầy đủ cả 2 điểm."
        )

        return EvaluationOutcome(
            misconception_repaired=True,
            explain_back_passed=is_pass,
            needs_support=not is_pass,
            confidence=0.9 if is_pass else 0.5,
            feedback=feedback,
            rubric_scores=rubric_scores,
        )
