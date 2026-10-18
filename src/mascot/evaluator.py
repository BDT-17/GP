"""Evaluator module for assessing misconception repair and explain-back against rubric."""

from __future__ import annotations

from typing import Dict, Tuple
from mascot.models import EvaluationOutcome


class Evaluator:
    """Evaluates learner inputs against misconception criteria and explain-back rubric."""

    def __init__(self, scenario_data: Dict):
        self.scenario = scenario_data
        self.concept_id = scenario_data.get("concept_id", "")
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

        if self.concept_id == "prog_param_passing":
            # Basic Programming: Pass-by-value vs Pass-by-reference
            has_val_point = any(p in text for p in [
                "bản sao", "copy", "sao chép", "không đổi biến ngoài", "không đổi",
                "không ảnh hưởng", "tham trị", "pass by value", "pass-by-value"
            ])
            has_ref_point = any(p in text for p in [
                "tham chiếu", "con trỏ", "địa chỉ", "ô nhớ", "pointer", "reference",
                "&", "*", "pass by reference", "pass-by-reference"
            ])

            if has_val_point and has_ref_point:
                return True, False, "Người học đã chỉ ra chính xác bản chất: tham trị sao chép biến, tham chiếu/con trỏ mới làm thay đổi biến gốc."
            elif has_val_point or has_ref_point:
                return False, needs_help, "Người học đã nêu được một khía cạnh, hãy làm rõ thêm cơ chế còn lại (tham trị vs tham chiếu/con trỏ)."
            else:
                return False, needs_help, "Người học chưa chỉ ra được lỗi sai trong phát biểu của bạn học."

        elif self.concept_id == "python_list_vs_tuple":
            # Python: List vs Tuple (Mutable vs Immutable)
            has_list_point = any(p in text for p in [
                "mutable", "thay đổi được", "sửa được", "thêm sửa xóa", "append",
                "thay đổi", "thêm phần tử", "sửa phần tử"
            ])
            has_tuple_point = any(p in text for p in [
                "immutable", "bất biến", "không thể thay đổi", "không sửa được",
                "cố định", "không đổi"
            ])

            if has_list_point and has_tuple_point:
                return True, False, "Người học đã phân biệt xuất sắc: List là Mutable (thay đổi được) còn Tuple là Immutable (bất biến)."
            elif has_list_point or has_tuple_point:
                return False, needs_help, "Người học đã nói đúng một phần, hãy nêu rõ tính chất của cả List và Tuple."
            else:
                return False, needs_help, "Người học chưa chỉ ra được lỗi sai trong phát biểu của bạn học."

        else:
            # Default: OOP Overloading vs Overriding
            mentions_same_class = any(p in text for p in [
                "cùng lớp", "cùng một lớp", "trong 1 lớp", "cùng class", "same class"
            ])
            mentions_diff_params = any(p in text for p in [
                "khác tham số", "khác kiểu", "số lượng tham số", "khác signature",
                "khác nhau về tham số", "different parameter"
            ])
            mentions_inheritance = any(p in text for p in [
                "kế thừa", "lớp cha", "lớp con", "cha con", "subclass",
                "superclass", "extends", "inheritance"
            ])
            mentions_same_signature = any(p in text for p in [
                "cùng tham số", "giống hệt", "giống tham số", "cùng tên và tham số",
                "same signature", "ghi đè lại"
            ])

            has_overloading_point = mentions_same_class or mentions_diff_params
            has_overriding_point = mentions_inheritance or mentions_same_signature

            if has_overloading_point and has_overriding_point:
                return True, False, "Người học đã chỉ ra thành công điểm khác biệt cốt lõi giữa Overloading và Overriding."
            elif has_overloading_point or has_overriding_point:
                return False, needs_help, "Người học đã nhận diện được một phần, nhưng cần làm rõ thêm khía cạnh còn lại."
            else:
                return False, needs_help, "Người học chưa chỉ ra được lỗi sai trong phát biểu của bạn học."

    def evaluate_explain_back(self, user_text: str) -> EvaluationOutcome:
        """Assesses learner's self-generated explain-back against rubric."""
        text = user_text.lower()

        if self.concept_id == "prog_param_passing":
            has_copy = any(p in text for p in ["bản sao", "copy", "sao chép", "ô nhớ mới"])
            has_address = any(p in text for p in ["địa chỉ", "ô nhớ", "tham chiếu", "con trỏ", "&", "*"])
            dim1 = has_copy and has_address

            has_no_side_effect = any(p in text for p in ["không đổi", "không thay đổi", "không ảnh hưởng"])
            has_side_effect = any(p in text for p in ["thay đổi", "biến gốc", "bên ngoài"])
            dim2 = has_no_side_effect and has_side_effect

            dim3 = any(p in text for p in ["&", "*", "con trỏ", "tham chiếu"])

            is_pass = dim1 and dim2
            rubric_scores = {
                "copy_vs_address": dim1,
                "side_effect_on_original": dim2,
                "syntax_distinction": dim3,
            }
            feedback = (
                "Giải thích xuất sắc và đầy đủ bản chất cơ chế truyền tham số!"
                if is_pass
                else "Bài giải thích còn thiếu cơ chế sao chép tham trị hoặc tác động lên biến gốc. Hãy bổ sung đầy đủ cả 2 điểm."
            )

        elif self.concept_id == "python_list_vs_tuple":
            has_list_mut = any(p in text for p in ["list", "danh sách"]) and any(p in text for p in ["mutable", "thay đổi"])
            has_tup_immut = any(p in text for p in ["tuple"]) and any(p in text for p in ["immutable", "bất biến", "không thay đổi", "không sửa"])
            dim1 = has_list_mut and has_tup_immut

            has_brackets = ("[" in text or "vuông" in text) and (")" in text or "tròn" in text)
            has_methods = any(p in text for p in ["append", "pop", "remove", "phương thức"])
            dim2 = has_brackets or has_methods

            dim3 = any(p in text for p in ["hash", "key", "bộ nhớ", "nhanh", "an toàn"])

            is_pass = dim1 and (dim2 or dim3)
            rubric_scores = {
                "mutability_contrast": dim1,
                "syntax_and_methods": dim2,
                "use_case_and_hashability": dim3,
            }
            feedback = (
                "Giải thích xuất sắc về tính chất Mutable của List và Immutable của Tuple!"
                if is_pass
                else "Bài giải thích cần nêu rõ tính biến đổi (mutable của list vs immutable của tuple) và cú pháp tương ứng."
            )

        else:
            # Default: OOP Overloading vs Overriding
            has_same_class = ("cùng" in text or "trong" in text or "same" in text) and ("lớp" in text or "class" in text)
            has_inheritance = any(p in text for p in ["kế thừa", "lớp cha", "lớp con", "cha con", "subclass", "superclass", "extends", "inheritance"])
            has_scope = has_same_class and has_inheritance

            has_diff_params = ("khác" in text or "different" in text) and ("tham số" in text or "parameter" in text or "signature" in text)
            has_same_params = ("cùng" in text or "giống" in text or "same" in text or "hệt" in text) and ("tham số" in text or "parameter" in text or "signature" in text or "tên" in text)
            has_signature = has_diff_params and has_same_params

            has_polymorphism_type = any(p in text for p in ["biên dịch", "compile", "thực thi", "runtime", "tĩnh", "động"])

            is_pass = has_scope and has_signature
            rubric_scores = {
                "scope_and_inheritance": has_scope,
                "method_signature": has_signature,
                "polymorphism_type": has_polymorphism_type,
            }
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
