"""FastAPI Web Server for MASCOT Demo with SQLite persistence."""

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mascot.course_manager import CourseManager
from mascot.database import DatabaseManager
from mascot.models import Role
from mascot.orchestrator import MascotOrchestrator

app = FastAPI(title="MASCOT Demo API", version="0.2.0")

# Persistence manager
db = DatabaseManager()

# Global orchestrator instance
orchestrator = MascotOrchestrator()
initial_peer_statement = orchestrator.start_session()

# Persist initial session & statement
def _sync_session_to_db(completed: bool = False):
    completed_at = datetime.now(timezone.utc).isoformat() if completed else None
    db.save_or_update_session(
        session_id=orchestrator.session_id,
        course_id=orchestrator.course_id,
        concept_id=orchestrator.concept_id,
        terminal_status=orchestrator.terminal_status.value,
        terminal_reason=orchestrator.terminal_reason,
        learner_attempts=orchestrator.learner_attempts,
        hint_count=orchestrator.hint_count,
        misconception_repaired=orchestrator.misconception_repaired,
        explain_back_passed=orchestrator.explain_back_passed,
        completed_at=completed_at,
    )

_sync_session_to_db()
db.add_chat_message(orchestrator.session_id, Role.PEER.value, initial_peer_statement)

# Static directory
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str


class SelectCourseRequest(BaseModel):
    course_id: str


class UpdateProfileRequest(BaseModel):
    xp_delta: int = 0
    gems_delta: int = 0
    streak_increment: bool = False
    hearts: Optional[int] = None


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
    """Switches current session to the requested course scenario and records in DB."""
    course_id = req.course_id.strip()
    initial_statement = orchestrator.switch_course(course_id)
    _sync_session_to_db()
    db.add_chat_message(orchestrator.session_id, Role.PEER.value, initial_statement)
    session_state = await get_session()
    return {
        "status": "switched",
        "course_id": orchestrator.course_id,
        "initial_statement": initial_statement,
        "session_state": session_state,
    }


@app.get("/api/session")
async def get_session():
    profile = db.get_learner_profile()
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
        "profile": profile,
        "code_snippet": orchestrator.scenario.get("code_snippet"),
    }


@app.post("/api/code/run")
async def run_code_simulation():
    """Simulates running the peer student's misconception code snippet."""
    snippet = orchestrator.scenario.get("code_snippet", {})
    return {
        "status": "success",
        "filename": snippet.get("filename", "demo.txt"),
        "language": snippet.get("language", "text"),
        "code": snippet.get("code", ""),
        "output": snippet.get("simulation_output", ""),
        "explanation": snippet.get("run_explanation", ""),
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống.")

    # Record user message to DB
    db.add_chat_message(orchestrator.session_id, Role.LEARNER.value, user_msg)

    # Process orchestrator turn
    result = orchestrator.process_turn(user_msg)

    # Record assistant response to DB
    db.add_chat_message(orchestrator.session_id, result["role"], result["message"])

    # Check completion and sync DB
    is_completed = orchestrator.terminal_status.value == "completed"
    _sync_session_to_db(completed=is_completed)

    # If completed, reward learner XP and Gems
    if is_completed:
        db.update_profile(xp_delta=50, gems_delta=15, streak_increment=True)

    session_state = await get_session()

    return {
        "reply": result,
        "session_state": session_state,
    }


@app.get("/api/profile")
async def get_profile():
    """Retrieves learner profile with streak, XP, gems, and league."""
    return db.get_learner_profile()


@app.post("/api/profile/update")
async def update_profile(req: UpdateProfileRequest):
    """Updates learner stats."""
    updated = db.update_learner_profile(
        xp_delta=req.xp_delta,
        gems_delta=req.gems_delta,
        streak_increment=req.streak_increment,
        hearts=req.hearts,
    )
    return updated


@app.get("/api/sessions")
async def get_all_sessions():
    """Retrieves all learning session records from database."""
    return {"sessions": db.get_all_sessions()}


@app.get("/api/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Retrieves all chat messages for a specific session."""
    return {"history": db.get_chat_history(session_id)}


@app.get("/api/llm/status")
async def get_llm_status():
    """Returns active LLM provider and status."""
    from mascot.llm_client import LLMClient
    client = LLMClient()
    return {
        "provider": client.get_provider(),
        "is_live_llm": client.get_provider() != "fallback",
    }


@app.get("/api/summary")
async def get_summary():
    summary = orchestrator.generate_instructor_summary()
    return summary.model_dump()


@app.post("/api/reset")
async def reset_session():
    global orchestrator
    orchestrator = MascotOrchestrator()
    msg = orchestrator.start_session()
    _sync_session_to_db()
    db.add_chat_message(orchestrator.session_id, Role.PEER.value, msg)
    return {"status": "reset_successful"}


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Đang khởi chạy MASCOT Demo Web Server...")
    print("👉 Mở trình duyệt tại: http://127.0.0.1:8000")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
