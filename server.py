"""FastAPI Web Server for MASCOT Demo."""

from pathlib import Path
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mascot.course_manager import CourseManager
from mascot.orchestrator import MascotOrchestrator

app = FastAPI(title="MASCOT Demo API", version="0.1.0")

# Global orchestrator instance
orchestrator = MascotOrchestrator()
orchestrator.start_session()

# Static directory
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str


class SelectCourseRequest(BaseModel):
    course_id: str


@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_file)


@app.get("/api/courses")
async def get_courses():
    """Returns list of available courses that have learning scenarios."""
    return {"courses": CourseManager.get_available_courses()}


@app.post("/api/session/select")
async def select_course(req: SelectCourseRequest):
    """Switches current session to the requested course scenario."""
    course_id = req.course_id.strip()
    initial_statement = orchestrator.switch_course(course_id)
    session_state = await get_session()
    return {
        "status": "switched",
        "course_id": orchestrator.course_id,
        "initial_statement": initial_statement,
        "session_state": session_state,
    }


@app.get("/api/session")
async def get_session():
    return {
        "session_id": orchestrator.session_id,
        "course_id": orchestrator.course_id,
        "lesson_id": orchestrator.lesson_id,
        "lesson_order": orchestrator.lesson_order,
        "concept_id": orchestrator.concept_id,
        "concept_title": orchestrator.scenario.get("concept_title", ""),
        "peer_name": orchestrator.scenario.get("peer_student", {}).get("name", "Bảo (Bạn học)"),
        "initial_misconception": orchestrator.scenario.get("peer_student", {}).get("initial_misconception", ""),
        "active_role": orchestrator.active_role.value,
        "learner_attempts": orchestrator.learner_attempts,
        "hint_count": orchestrator.hint_count,
        "misconception_repaired": orchestrator.misconception_repaired,
        "explain_back_passed": orchestrator.explain_back_passed,
        "terminal_status": orchestrator.terminal_status.value,
        "terminal_reason": orchestrator.terminal_reason,
        "conversation_history": orchestrator.conversation_history,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống.")

    result = orchestrator.process_turn(user_msg)
    session_state = await get_session()

    return {
        "reply": result,
        "session_state": session_state,
    }


@app.get("/api/summary")
async def get_summary():
    summary = orchestrator.generate_instructor_summary()
    return summary.model_dump()


@app.post("/api/reset")
async def reset_session():
    global orchestrator
    orchestrator = MascotOrchestrator()
    orchestrator.start_session()
    return {"status": "reset_successful"}


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Đang khởi chạy MASCOT Demo Web Server...")
    print("👉 Mở trình duyệt tại: http://127.0.0.1:8000")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)

