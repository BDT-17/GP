"""Session orchestrator managing state transitions, turn-taking, and stopping conditions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from mascot.agents import LecturerAgent, PeerAgent, TeachingAssistantAgent
from mascot.course_manager import CourseManager
from mascot.evaluator import Evaluator
from mascot.models import (
    Citation,
    InstructorSummary,
    Role,
    SessionEvent,
    TerminalStatus,
)
from mascot.retriever import CurriculumRetriever
from mascot.security import AdversarialGuard


class MascotOrchestrator:
    """Orchestrates classroom simulation obeying all MVP product rules (AC1-AC7)."""

    def __init__(
        self,
        course_id: Optional[str] = None,
        scenario_path: Optional[Path] = None,
        corpus_path: Optional[Path] = None,
    ):
        if scenario_path is None or corpus_path is None:
            resolved_scenario, resolved_corpus = CourseManager.resolve_paths(course_id)
            if scenario_path is None:
                scenario_path = resolved_scenario
            if corpus_path is None:
                corpus_path = resolved_corpus

        with open(scenario_path, "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

        self.retriever = CurriculumRetriever(corpus_path=corpus_path)
        self.evaluator = Evaluator(self.scenario)
        self.security_guard = AdversarialGuard()

        self.peer = PeerAgent(
            name=self.scenario["peer_student"]["name"],
            initial_misconception=self.scenario["peer_student"]["initial_misconception"],
        )
        self.ta = TeachingAssistantAgent()
        self.lecturer = LecturerAgent()

        # Session state
        self.session_id = str(uuid.uuid4())
        self.course_id = self.scenario["course_id"]
        self.lesson_id = self.scenario["lesson_id"]
        self.lesson_order = self.scenario["lesson_order"]
        self.concept_id = self.scenario["concept_id"]
        self.scenario_id = self.scenario["scenario_id"]

        self.active_role: Role = Role.PEER
        self.learner_attempts: int = 0
        self.hint_count: int = 0
        self.escalation_count: int = 0
        self.misconception_repaired: bool = False
        self.explain_back_passed: bool = False
        self.terminal_status: TerminalStatus = TerminalStatus.ACTIVE
        self.terminal_reason: str = ""
        self.citations_used: List[Citation] = []
        self.security_alerts: List[Dict[str, Any]] = []

        self.event_log: List[SessionEvent] = []
        self.conversation_history: List[Dict[str, str]] = []

    def _log_event(self, event_type: str, role: Optional[str] = None, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        event = SessionEvent(
            event_type=event_type,
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.event_log.append(event)

    def start_session(self) -> str:
        """Starts session with Peer stating the configured misconception."""
        msg = self.peer.get_initial_statement()
        self.active_role = Role.PEER
        self.conversation_history.append({"role": Role.PEER.value, "content": msg})
        self._log_event(
            event_type="role_transition",
            role=Role.PEER.value,
            content=msg,
            metadata={"stage": "initial_misconception"},
        )
        return msg

    def switch_course(self, course_id: str) -> str:
        """Switches active course, reloads its scenario and corpus, and restarts the session."""
        scenario_path, corpus_path = CourseManager.resolve_paths(course_id)
        with open(scenario_path, "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

        self.retriever = CurriculumRetriever(corpus_path=corpus_path)
        self.evaluator = Evaluator(self.scenario)

        self.peer = PeerAgent(
            name=self.scenario["peer_student"]["name"],
            initial_misconception=self.scenario["peer_student"]["initial_misconception"],
        )
        self.ta = TeachingAssistantAgent()
        self.lecturer = LecturerAgent()

        # Reset session state
        self.session_id = str(uuid.uuid4())
        self.course_id = self.scenario["course_id"]
        self.lesson_id = self.scenario["lesson_id"]
        self.lesson_order = self.scenario["lesson_order"]
        self.concept_id = self.scenario["concept_id"]
        self.scenario_id = self.scenario["scenario_id"]

        self.active_role = Role.PEER
        self.learner_attempts = 0
        self.hint_count = 0
        self.escalation_count = 0
        self.misconception_repaired = False
        self.explain_back_passed = False
        self.terminal_status = TerminalStatus.ACTIVE
        self.terminal_reason = ""
        self.citations_used = []
        self.security_alerts = []

        self.event_log = []
        self.conversation_history = []

        return self.start_session()

    def process_turn(self, learner_text: str) -> Dict[str, Any]:
        """Processes one learner turn.

        Ensures AC5: Exactly one authorized speaking role produces the next response.
        """
        if self.terminal_status != TerminalStatus.ACTIVE:
            return {
                "role": Role.ORCHESTRATOR.value,
                "message": f"Buổi học đã kết thúc với trạng thái: {self.terminal_status.value} ({self.terminal_reason}).",
                "terminal": True,
            }

        self.learner_attempts += 1
        self.conversation_history.append({"role": Role.LEARNER.value, "content": learner_text})
        self._log_event(
            event_type="learner_input",
            role=Role.LEARNER.value,
            content=learner_text,
            metadata={"attempt_number": self.learner_attempts},
        )

        # 0. Adversarial & Security Inspection (AC6, P1)
        scan = self.security_guard.inspect(learner_text)
        if scan.is_suspicious:
            alert = {
                "turn": self.learner_attempts,
                "threat_type": scan.threat_type,
                "reason": scan.reason,
                "input_snippet": learner_text[:100],
            }
            self.security_alerts.append(alert)
            self._log_event(
                event_type="security_alert",
                role=Role.ORCHESTRATOR.value,
                content=scan.reason,
                metadata=alert,
            )

        if scan.is_blocked:
            response_text = scan.safe_response or "[Hệ thống]: Yêu cầu bị từ chối do vi phạm quy tắc an toàn sư phạm."
            self.active_role = Role.ORCHESTRATOR
            self._log_event(event_type="response_generated", role=Role.ORCHESTRATOR.value, content=response_text)
            self.conversation_history.append({"role": Role.ORCHESTRATOR.value, "content": response_text})
            return {
                "role": Role.ORCHESTRATOR.value,
                "message": response_text,
                "terminal": False,
            }

        # 1. Apply Curriculum Gate check (AC1, AC2)
        retrieval_decision = self.retriever.retrieve(
            query=learner_text,
            current_lesson_order=self.lesson_order,
            concept_id=self.concept_id,
        )

        self._log_event(
            event_type="retrieval_decision",
            metadata={
                "is_authorized": retrieval_decision.is_authorized,
                "status": retrieval_decision.status,
                "reason": retrieval_decision.reason,
            },
        )

        if not retrieval_decision.is_authorized:
            # AC2: Future content or out of scope refusal/redirect
            response_text = f"[Hệ thống - Chuyển hướng]: {retrieval_decision.reason}"
            self.active_role = Role.ORCHESTRATOR
            self._log_event(event_type="response_generated", role=Role.ORCHESTRATOR.value, content=response_text)
            self.conversation_history.append({"role": Role.ORCHESTRATOR.value, "content": response_text})
            return {
                "role": Role.ORCHESTRATOR.value,
                "message": response_text,
                "terminal": False,
            }

        # Save citations if authorized
        for cit in retrieval_decision.citations:
            if cit.chunk_id not in [c.chunk_id for c in self.citations_used]:
                self.citations_used.append(cit)

        # 2. Evaluation & Turn Routing
        if not self.misconception_repaired:
            # Stage A: Evaluating misconception repair
            repaired, needs_help, eval_feedback = self.evaluator.evaluate_repair_attempt(learner_text)
            self._log_event(
                event_type="assessment",
                metadata={"stage": "misconception_repair", "repaired": repaired, "needs_help": needs_help},
            )

            if repaired:
                self.misconception_repaired = True
                self.active_role = Role.PEER
                response_text = self.peer.acknowledge_repair(
                    self.scenario.get("concept_title"), learner_input=learner_text
                )
            else:
                # Needs support or failed attempt
                self.hint_count += 1
                max_hints = self.scenario["escalation_policy"]["max_hints_before_escalation"]

                if self.hint_count > max_hints:
                    # AC4: Escalation to Lecturer
                    self.active_role = Role.LECTURER
                    self.escalation_count += 1
                    response_text = self.lecturer.provide_clarification(
                        retrieval_decision.citations,
                        concept_title=self.scenario.get("concept_title"),
                        learner_input=learner_text,
                    )
                else:
                    # AC3: TA Socratic hint
                    self.active_role = Role.TA
                    response_text = self.ta.get_hint(
                        self.hint_count,
                        learner_input=learner_text,
                        concept_title=self.scenario.get("concept_title"),
                    )

        else:
            # Stage B: Evaluating Explain-Back (AC6)
            eval_outcome = self.evaluator.evaluate_explain_back(learner_text)
            self._log_event(
                event_type="assessment",
                metadata={
                    "stage": "explain_back",
                    "passed": eval_outcome.explain_back_passed,
                    "scores": eval_outcome.rubric_scores,
                },
            )

            if eval_outcome.explain_back_passed:
                self.explain_back_passed = True
                self.terminal_status = TerminalStatus.COMPLETED
                self.terminal_reason = "Người học đã sửa thành công hiểu lầm và hoàn thành bài giải thích lại đạt chuẩn rubric."
                self.active_role = Role.ORCHESTRATOR
                response_text = (
                    "🎉 **Chúc mừng bạn đã hoàn thành xuất sắc buổi học!**\n\n"
                    "Bạn đã giúp bạn học nhận ra sai sót và tự mình giải thích rất chuẩn xác về "
                    f"bản chất của {self.scenario.get('concept_title', 'bài học')}.\n\n"
                    "Buổi học chính thức kết thúc."
                )
            else:
                self.active_role = Role.TA
                response_text = self.ta.prompt_explain_back_retry(learner_input=learner_text)

        # Log and record single speaking turn (AC5)
        self._log_event(event_type="response_generated", role=self.active_role.value, content=response_text)
        self.conversation_history.append({"role": self.active_role.value, "content": response_text})

        return {
            "role": self.active_role.value,
            "message": response_text,
            "terminal": self.terminal_status == TerminalStatus.COMPLETED,
        }

    def generate_instructor_summary(self) -> InstructorSummary:
        """Generates concise instructor-facing summary (AC7)."""
        return InstructorSummary(
            session_id=self.session_id,
            course_id=self.course_id,
            lesson_id=self.lesson_id,
            concept_id=self.concept_id,
            scenario_id=self.scenario_id,
            learner_attempts=self.learner_attempts,
            hint_count=self.hint_count,
            escalated_to_lecturer=self.escalation_count > 0,
            misconception_repaired=self.misconception_repaired,
            explain_back_passed=self.explain_back_passed,
            terminal_status=self.terminal_status,
            terminal_reason=self.terminal_reason or "Session in progress or ended.",
            citations_used=[c.source_location for c in self.citations_used],
            security_alerts=self.security_alerts,
            created_at=self.event_log[0].timestamp if self.event_log else "",
        )

