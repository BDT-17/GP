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

## Change log

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
