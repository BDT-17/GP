"""Pydantic data models for MASCOT state, curriculum metadata, and events."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    LEARNER = "learner"
    PEER = "peer"
    TA = "ta"
    LECTURER = "lecturer"
    EVALUATOR = "evaluator"
    ORCHESTRATOR = "orchestrator"


class TerminalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABSTAINED = "abstained"
    REFUSED = "refused"


class LessonChunk(BaseModel):
    chunk_id: str
    course_id: str
    lesson_id: str
    lesson_order: int
    concept_id: str
    source_id: str
    source_location: str
    text: str


class Citation(BaseModel):
    source_id: str
    source_location: str
    chunk_id: str
    reference_snippet: str


class RetrievalDecision(BaseModel):
    is_authorized: bool
    status: str  # "allowed", "denied_future_content", "insufficient_evidence", "out_of_scope"
    reason: str
    citations: List[Citation] = Field(default_factory=list)
    chunks: List[LessonChunk] = Field(default_factory=list)


class EvaluationOutcome(BaseModel):
    misconception_repaired: bool
    explain_back_passed: bool
    needs_support: bool
    confidence: float
    feedback: str
    rubric_scores: Dict[str, bool] = Field(default_factory=dict)


class SessionEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str  # "learner_input", "retrieval_decision", "role_transition", "response_generated", "assessment", "terminal_transition"
    role: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InstructorSummary(BaseModel):
    session_id: str
    course_id: str
    lesson_id: str
    concept_id: str
    scenario_id: str
    learner_attempts: int
    hint_count: int
    escalated_to_lecturer: bool
    misconception_repaired: bool
    explain_back_passed: bool
    terminal_status: TerminalStatus
    terminal_reason: str
    citations_used: List[str]
    created_at: str

