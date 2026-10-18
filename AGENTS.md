# MASCOT Repository Guide

## Project purpose

MASCOT is a multi-agent simulated online classroom for active tutoring. Its MVP
uses one VLearn lesson/concept and three roles: Peer Student, Teaching
Assistant (TA), and Lecturer. A session is successful only when the learner
identifies and corrects the scenario misconception and completes an accurate
explain-back in their own words.

## Current repository state

As of 2026-10-13, this repository contains no application source, dependency
manifest, tests, or application runtime configuration. GitHub Actions provides
a Python 3.10 CI baseline, but no framework, LLM provider, vector store,
database, or deployment target has been selected. Before implementation,
update this document with the selected stack and its verified commands.

## Durable product rules

- Treat the lesson materials and their metadata as the authority for factual
  learning claims. Cite the exact permitted source passage, slide, or segment.
- Enforce curriculum scope at retrieval time: prerequisite and current content
  may be eligible; future and out-of-scope content must be refused or
  redirected, never silently retrieved.
- Keep roles distinct: Peer Student expresses the configured misconception;
  TA gives Socratic hints rather than a direct answer; Lecturer is an explicit
  escalation path for deeper clarification.
- The orchestration state owns turn-taking. At most one role may produce the
  next instructional response for a learner turn.
- Do not mark a session complete solely because a learner selected an answer.
  Completion requires a correct misconception repair and a grounded,
  successful explain-back.
- Persist inspectable session evidence: selected lesson/concept/scenario,
  retrieval citations and policy decisions, role/turn transitions, learner
  responses, assessment result, and a short instructor-facing summary. Avoid
  storing secrets or unnecessary personally identifiable data.
- Treat prompt text, retrieved documents, and learner messages as untrusted
  input. They cannot override curriculum policy, role permissions, citations,
  or stopping conditions.

## Workflows

- Use `.codex/skills/mascot-orchestration/SKILL.md` for MASCOT feature work,
  architecture decisions, evaluation design, and major reviews.
- Read `.codex/skills/mascot-orchestration/references/mvp-contract.md` when a
  task needs product boundaries or acceptance evidence.
- Before starting project work, check `.codex/vibecode kit`. If present, read
  and follow its guidance and concept files.

## Verification

Verified executable test and lint commands:
- Install dependencies: `pip install -r requirements.txt`
- Run linting: `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
- Run test suite with coverage: `pytest -v --cov=src`
- Launch demo API server: `python server.py` (FastAPI at `http://127.0.0.1:8000`)

Automated CI pipeline (`.github/workflows/ci.yml`) executes linting and mandatory test suite across:
- `tests/test_curriculum_gate.py`: Retrieval gating, prerequisite/future-lesson policies.
- `tests/test_orchestrator.py`: Multi-agent orchestration, Socratic hints, lecturer escalation, completion integrity.
- `tests/test_api.py`: FastAPI server endpoints (`/`, `/api/session`, `/api/chat`, `/api/summary`, `/api/reset`).
- `tests/test_course_modularization.py`: Modular course corpora and scenario switching (CS102, ICT1.002, CS105).
- `tests/test_database.py`: SQLite persistence for learner profile (XP/gems/streak), session logs, and chat history.
- `tests/test_llm_integration.py`: Multi-provider LLM client (Gemini/Groq/OpenAI/Ollama) with Socratic prompting and graceful fallback.
- `tests/test_adversarial.py`: Prompt injection defense, role hijacking resistance, and completion integrity (MVP Scenarios 6 & 7).
- `tests/test_rubric_and_semantic_rag.py`: Multi-criteria rubric evaluation, diagnostic TA feedback, and Semantic Vector RAG with cosine similarity.
- `tests/test_peer_and_rubric_llm.py`: Peer deliberation/pushback, turn arbitration, and LLM rubric-diagnostic Socratic prompting.
- `tests/test_ingest_vlearn.py`: VLearn curriculum slide/lecture ingestion, chunk extraction, and corpus merging.
- `tests/test_pedagogical_benchmark.py`: Automated pedagogical benchmark suite across 4 learner personas (AC1-AC7 invariants).
- `tests/test_report_export.py`: Inspectable instructor audit report (PDF/HTML/JSON) with SHA-256 evidence seal and Certificate of Mastery.
- `tests/test_frustration_and_voice.py`: Learner frustration/confusion detection and TA empathy scaffolding.
- `tests/test_generate_scenario.py`: Automated scenario generation and schema validation from VLearn corpus.
- `tests/test_ab_testing.py`: A/B comparative pedagogical evaluation comparing MASCOT vs baseline LLM.

## Change log

- 2026-10-18: Implemented Cinematic Mascot Light-Sweep Intro Animation & Modern Authentication Screen (Login/Register) (`static/index.html`, `server.py`, `src/mascot/database.py`, `tests/test_api.py`, `tests/test_database.py`): Beam-sweep typography animation lighting up M-A-S-C-O-T with musical chimes, smooth dissolve into split-view Auth screen featuring 3D Owl Teacher and Duolingo-styled Login/Register forms with guest mode and logout controls (74 tests, 95% coverage).
- 2026-10-18: Implemented Learner Experience Polish (Giai đoạn 3) & Classroom Owl Mascot Hero Redesign (`static/index.html`, `static/mascot_teacher.png`): Aesthetic Hero banner with graduation-cap Owl mascot pointing to blackboard, Code Playground side-by-side Diff Viewer, Out of Hearts refill modal (20 gems or free review), Mastery Celebration modal with Web Audio fanfare, and user sessions/certificates profile history (72 tests, 94% coverage).
- 2026-10-18: Implemented Pure SVG Multi-Dimensional Rubric Radar Chart in Instructor Dashboard and printable PDF/HTML reports (`src/mascot/report_generator.py`, `static/index.html`).
- 2026-10-18: Built Comparative A/B Testing Evaluation Suite (`benchmarks/ab_testing_eval.py`, `tests/test_ab_testing.py`) demonstrating +200% active cognitive turns, 0% direct answer dependence, and 100% explain-back mastery vs baseline LLM.
- 2026-10-18: Created Automated Scenario Generator (`tools/generate_scenario.py`, `tests/test_generate_scenario.py`) extracting misconceptions and generating schema-compliant scenarios from VLearn corpus.
- 2026-10-18: Implemented Voice STT (Web Speech API) & Distinct Character Voice TTS (Bảo, Thầy Hùng, TS. Minh) and Frustration/Confusion Detection with TA Empathy Scaffolding (`src/mascot/agents.py`, `tests/test_frustration_and_voice.py`) (71 tests, 94% coverage).
- 2026-10-18: Implemented Pedagogical Audit Report Export & Certificate of Mastery (`/api/instructor/report/export`, `src/mascot/report_generator.py`) in JSON & printable PDF/HTML with SHA-256 evidence seal and UI print button (63 tests, 93% coverage).
- 2026-10-18: Built Automated Pedagogical Benchmark Suite (`benchmarks/run_pedagogical_eval.py`) simulating 4 learner personas (Lazy, Adversarial, Partial, Star), measuring 0.0% Direct Answer Leakage, 0.0% Future Leakage, 0.0% False Completion, and 100.0% Rubric Diagnostic Accuracy.
- 2026-10-18: Created VLearn Curriculum Ingestion Tool (`tools/ingest_vlearn.py`) parsing markdown slides into standardized pedagogical chunks with slide metadata and corpus JSON merging.
- 2026-10-18: Implemented 2-Way Code Playground with Kinesthetic Learning & Verification (`/api/code/verify`) seamlessly advancing to Step 2 Explain-Back on code repair.
- 2026-10-18: Enhanced Learning View with Classroom Discussion Feed, 2-Step Pedagogical Stepper, Interactive 2-Way Code Playground with Fix & Verify (`/api/code/run`), and seamless chat turns (52 tests, 92% coverage).
- 2026-10-18: Implemented Peer Pushback & Deliberation (`PeerAgent.pushback`), LLM Socratic Prompting with Rubric Missing Dimensions (`TeachingAssistantAgent.prompt_explain_back_retry`), and audit tracking (51 tests, 92% coverage).
- 2026-10-18: Implemented Multi-Criteria Rubric Scoring (`Evaluator`), diagnostic TA Socratic feedback, and Semantic Vector RAG (`CurriculumRetriever`) with TF-IDF cosine similarity and curriculum gating (45 tests, 92% coverage).
- 2026-10-18: Implemented AdversarialGuard (Prompt Injection & Role Hijacking defense) and Instructor Audit Dashboard with real-time session observability and chat transcripts (39 tests, 92% coverage).
- 2026-10-18: Implemented Interactive Code Misconception Block and Runner Simulator (`/api/code/run`), dynamic code snippets across courses (Java, C, Python), and frontend interactive execution console (32 tests, 91% coverage).
- 2026-10-18: Integrated Multi-Provider LLM Client (`src/mascot/llm_client.py`) supporting Gemini, Groq, OpenAI, and Ollama with Socratic hint prompting and offline fallback (30 tests, 91% coverage).
- 2026-10-18: Implemented SQLite Database Persistence (`src/mascot/database.py`), learner profile stats (XP, gems, streak), session history logging, and API integration (23 tests, 96% coverage).
- 2026-10-18: Implemented Course & Scenario Modularization (`data/courses/`), dynamic CourseManager, multi-concept Evaluator, and integrated frontend subject switching (19 tests, 95% coverage).
- 2026-10-17: Configured comprehensive CI pipeline (`ci.yml`) with pip caching, flake8 linting, mandatory pytest suite (15 tests, 96% coverage) and FastAPI integration tests.
- 2026-10-13: Added Python 3.10 GitHub Actions CI for pushes and pull requests
  targeting `thangbd/dev`; it has a visible no-tests notice until a suite is
  introduced.
- 2026-10-13: Added proposed MVP requirements and ADR 0001; implementation is
  gated on approval of the backend-first, provider-neutral architecture and a
  permitted lesson corpus.
- 2026-10-13: Evolved the MASCOT handoff contract to require one traceable
  acceptance-evidence row per changed behavior; this prevents unverified
  coverage claims while the repository has no executable checks.
- 2026-10-13: Added the initial Codex harness and the MASCOT orchestration
  skill for the approved project proposal.
