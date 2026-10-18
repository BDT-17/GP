"""SQLite Database persistence for MASCOT learning state, user profile, and chat history."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "mascot.db"


class DatabaseManager:
    """Manages SQLite database operations for learner profiles, sessions, and chat history."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initializes database schema and ensures default learner profile exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Learner Profile Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learner_profile (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    streak INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 568,
                    gems INTEGER DEFAULT 772,
                    hearts INTEGER DEFAULT 3,
                    league TEXT DEFAULT 'Silver',
                    top3_finishes INTEGER DEFAULT 1,
                    last_active_date TEXT
                )
            """)

            # 2. Learning Sessions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    session_id TEXT PRIMARY KEY,
                    course_id TEXT NOT NULL,
                    concept_id TEXT NOT NULL,
                    terminal_status TEXT NOT NULL,
                    terminal_reason TEXT,
                    learner_attempts INTEGER DEFAULT 0,
                    hint_count INTEGER DEFAULT 0,
                    misconception_repaired INTEGER DEFAULT 0,
                    explain_back_passed INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)

            # 3. Chat History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES learning_sessions (session_id)
                )
            """)

            # Seed default learner if table is empty
            cursor.execute("SELECT COUNT(*) as cnt FROM learner_profile WHERE id = 1")
            row = cursor.fetchone()
            if row["cnt"] == 0:
                cursor.execute("""
                    INSERT INTO learner_profile (id, username, display_name, streak, xp, gems, hearts, league, top3_finishes, last_active_date)
                    VALUES (1, 'QuocAnh162480', 'Quoc Anh', 1, 568, 772, 3, 'Silver', 1, ?)
                """, (datetime.now(timezone.utc).isoformat(),))

            conn.commit()

    def get_learner_profile(self, user_id: int = 1) -> Dict[str, Any]:
        """Fetches profile for given user_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learner_profile WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}

    def update_learner_profile(
        self,
        user_id: int = 1,
        xp_delta: int = 0,
        gems_delta: int = 0,
        streak_increment: bool = False,
        hearts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Updates learner stats and returns updated profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learner_profile WHERE id = ?", (user_id,))
            current = cursor.fetchone()
            if not current:
                return {}

            new_xp = max(0, current["xp"] + xp_delta)
            new_gems = max(0, current["gems"] + gems_delta)
            new_streak = current["streak"] + (1 if streak_increment else 0)
            new_hearts = hearts if hearts is not None else current["hearts"]
            now_iso = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                UPDATE learner_profile
                SET xp = ?, gems = ?, streak = ?, hearts = ?, last_active_date = ?
                WHERE id = ?
            """, (new_xp, new_gems, new_streak, new_hearts, now_iso, user_id))
            conn.commit()

        return self.get_learner_profile(user_id)

    def save_or_update_session(
        self,
        session_id: str,
        course_id: str,
        concept_id: str,
        terminal_status: str,
        terminal_reason: str = "",
        learner_attempts: int = 0,
        hint_count: int = 0,
        misconception_repaired: bool = False,
        explain_back_passed: bool = False,
        created_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ) -> None:
        """Inserts or updates a learning session row."""
        if not created_at:
            created_at = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_sessions (
                    session_id, course_id, concept_id, terminal_status, terminal_reason,
                    learner_attempts, hint_count, misconception_repaired, explain_back_passed,
                    created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    terminal_status = excluded.terminal_status,
                    terminal_reason = excluded.terminal_reason,
                    learner_attempts = excluded.learner_attempts,
                    hint_count = excluded.hint_count,
                    misconception_repaired = excluded.misconception_repaired,
                    explain_back_passed = excluded.explain_back_passed,
                    completed_at = excluded.completed_at
            """, (
                session_id, course_id, concept_id, terminal_status, terminal_reason,
                learner_attempts, hint_count, 1 if misconception_repaired else 0,
                1 if explain_back_passed else 0, created_at, completed_at
            ))
            conn.commit()

    def add_chat_message(self, session_id: str, role: str, content: str) -> None:
        """Appends a chat turn message to database."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, now_iso))
            conn.commit()

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves all chat messages for a given session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_id, role, content, created_at
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Retrieves history of all learning sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM learning_sessions
                ORDER BY created_at DESC
            """)
            return [dict(r) for r in cursor.fetchall()]
