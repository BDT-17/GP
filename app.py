"""Streamlit Web Demo for MASCOT (Multi-Agent Simulated Classroom for Online Tutoring)."""

import json
import os
import sys
from pathlib import Path
import streamlit as st

# Ensure src is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mascot.models import Role, TerminalStatus
from mascot.orchestrator import MascotOrchestrator

# Set page config
st.set_page_config(
    page_title="MASCOT - Lớp học mô phỏng AI",
    page_icon="🎓",
    layout="wide",
)

# Custom CSS for clean UI
st.markdown(
    """
    <style>
    .role-badge-peer { background-color: #e8f5e9; color: #2e7d32; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .role-badge-ta { background-color: #fff3e0; color: #ef6c00; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .role-badge-lecturer { background-color: #f3e5f5; color: #7b1fa2; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .role-badge-system { background-color: #eceff1; color: #37474f; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = MascotOrchestrator()
    initial_msg = st.session_state.orchestrator.start_session()
    st.session_state.messages = [
        {"role": Role.PEER.value, "content": initial_msg}
    ]

orch: MascotOrchestrator = st.session_state.orchestrator

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎓 MASCOT Classroom")
    st.caption("Multi-Agent Simulated Classroom for Online Tutoring")
    
    st.divider()
    st.subheader("📚 Thông tin bài học")
    st.write(f"**Môn học:** {orch.course_id}")
    st.write(f"**Bài học:** {orch.lesson_id} (Thứ tự: {orch.lesson_order})")
    st.write(f"**Khái niệm:** {orch.scenario['concept_title']}")

    st.divider()
    st.subheader("📊 Tiến trình học tập (Active Learning)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Lượt gửi", orch.learner_attempts)
    with col2:
        st.metric("Gợi ý TA", f"{orch.hint_count}/2")

    st.checkbox("1. Nhận diện hiểu lầm của bạn học", value=True, disabled=True)
    st.checkbox("2. Sửa lỗi sai cho bạn học", value=orch.misconception_repaired, disabled=True)
    st.checkbox("3. Giải thích lại (Explain-Back)", value=orch.explain_back_passed, disabled=True)

    if orch.terminal_status == TerminalStatus.COMPLETED:
        st.success("🎉 Buổi học hoàn thành!")
    elif orch.escalation_count > 0:
        st.warning("⚠️ Đã chuyển lên Giảng viên (Escalated)")

    st.divider()
    with st.expander("📖 Xem tài liệu bài giảng được cấp phép"):
        for chunk in orch.retriever.chunks:
            if chunk.lesson_order <= orch.lesson_order:
                st.markdown(f"**{chunk.source_location}**")
                st.caption(chunk.text)
                st.divider()

    st.divider()
    summary = orch.generate_instructor_summary()
    st.download_button(
        label="📥 Tải báo cáo cho Giảng viên (JSON)",
        data=json.dumps(summary.model_dump(), indent=2, ensure_ascii=False),
        file_name=f"mascot_summary_{orch.session_id[:8]}.json",
        mime="application/json",
    )

    if st.button("🔄 Khởi động lại phiên học"):
        st.session_state.orchestrator = MascotOrchestrator()
        new_msg = st.session_state.orchestrator.start_session()
        st.session_state.messages = [
            {"role": Role.PEER.value, "content": new_msg}
        ]
        st.rerun()

# --- MAIN CHAT AREA ---
st.header("Lớp học tương tác mô phỏng")
st.info(
    "💡 **Nhiệm vụ của bạn:** Phát hiện lỗi sai trong phát biểu của bạn học Bảo, "
    "hướng dẫn bạn ấy sửa sai, và tự mình giải thích lại bản chất để hoàn thành buổi học."
)

role_avatars = {
    Role.LEARNER.value: "👤",
    Role.PEER.value: "🧑‍🎓",
    Role.TA.value: "👨‍🏫",
    Role.LECTURER.value: "🎓",
    Role.ORCHESTRATOR.value: "🤖",
}

for msg in st.session_state.messages:
    role = msg["role"]
    avatar = role_avatars.get(role, "💬")
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Nhập câu trả lời hoặc câu hỏi của bạn..."):
    # Append learner message
    st.session_state.messages.append({"role": Role.LEARNER.value, "content": prompt})
    with st.chat_message(Role.LEARNER.value, avatar="👤"):
        st.markdown(prompt)

    # Process through MascotOrchestrator
    result = orch.process_turn(prompt)
    bot_role = result["role"]
    bot_message = result["message"]

    st.session_state.messages.append({"role": bot_role, "content": bot_message})
    with st.chat_message(bot_role, avatar=role_avatars.get(bot_role, "💬")):
        st.markdown(bot_message)

    if result.get("terminal"):
        st.balloons()
        st.rerun()

