# MASCOT MVP Product Specification

**Status:** proposed — implementation blocked pending architecture approval
**Audience:** MASCOT student team and supervisor
**Source of truth:** approved group-project proposal; this document
**Owner:** project team
**Review point:** before repository bootstrap and whenever the lesson corpus or
deployment target changes

## Outcome

Build a demonstrable tutoring session for one instructor-selected VLearn
concept. The learner must detect and correct a Peer Student's configured
misconception, receive Socratic support from a Teaching Assistant (TA) when
needed, and successfully explain the concept back before the session ends.

Success is not a fluent chat response. It is a session with grounded,
curriculum-authorized evidence, a valid role/turn trace, and an explain-back
outcome that an instructor can review.

## Scope

### Must have

- One course, lesson, concept, and scenario selected by an instructor.
- Ingestion of the associated transcript and/or slides into chunks carrying
  `course_id`, `lesson_id`, `concept_id`, `source_id`, `source_location`, and
  `lesson_order` metadata.
- Curriculum gate: prerequisite and current lesson chunks can be retrieved;
  future and out-of-scope chunks cannot be used in an instructional answer.
- LangGraph-managed roles: Peer Student, TA, and Lecturer.
- A single session state authority, one authorized speaking role per learner
  turn, and named escalation/stopping conditions.
- Citation-bearing factual instructional responses, or an explicit abstain or
  redirect when permitted evidence is insufficient.
- Misconception-repair and explain-back checkpoints before completion.
- Session event log and a concise instructor-facing summary.

### Explicitly deferred

- More than one lesson/concept, automatic curriculum authoring, learner
  profiling, gradebook/LMS integration, and high-stakes grading.
- Production authentication, multi-tenant hosting, and permanent personal-data
  retention. A future deployment decision must add these before collecting
  identifiable learner data.
- Automatic extraction quality guarantees for arbitrary PDF/slides.

## Actors and responsibilities

| Actor | Can do | Cannot do |
| --- | --- | --- |
| Learner | answer, request help, ask a relevant question, provide explain-back | override curriculum/role policy |
| Instructor/configurator | choose lesson, concept, sources, scenario, and escalation policy | silently make future content available |
| Peer Student | state the configured misconception and respond as a peer | teach, grade, or change the scenario |
| TA | ask Socratic questions and give graduated hints | give the answer before policy permits or complete the session |
| Lecturer | give deeper, grounded clarification after escalation | bypass citations or curriculum policy |
| Orchestrator | route turns, apply gates, persist state/events, terminate | generate an ungrounded instructional answer |

## Session flow

```text
configured scenario → Peer Student misconception → learner attempt
                                             ↓
                       correct repair? ─yes→ explain-back assessment
                             │                     │
                             no                    pass → completed summary
                             ↓                      │
                  TA Socratic hint / question       fail → TA or Lecturer path
                             │
                   named escalation condition? ─yes→ Lecturer clarification
```

Every possible route first applies the curriculum gate and evidence retrieval;
an insufficient-evidence result terminates that response as abstain/redirect,
not as an answer.

## State and events

The minimum session state is:

```text
session_id, selected_course, selected_lesson, selected_concept, scenario_id,
active_role, learner_attempts, hint_count, escalation_count,
retrieval_decisions, citations, misconception_repaired,
explain_back_result, terminal_reason
```

Persist an append-only event for each learner input, retrieval authorization
decision, retrieved evidence reference, role transition, generated response,
assessment, and terminal transition. Log references and policy outcomes, not
provider secrets or unnecessary raw personal data.

## Acceptance criteria

1. **Grounded current content:** Given a factual question about the selected
   concept, when a permitted chunk supports it, then the response includes a
   resolvable source citation and the event log records the allowed retrieval.
2. **Future-content denial:** Given a question requiring a later lesson, when
   retrieval runs, then no future chunk is supplied to generation and the
   learner receives a logged redirect/refusal.
3. **TA behavior:** Given an incorrect or incomplete repair, when the learner
   requests help, then the TA asks a relevant Socratic question or gives a
   bounded hint rather than immediately stating the solution.
4. **Lecturer escalation:** Given the configured escalation condition, when it
   is satisfied, then the next authorized instructional role is Lecturer and
   its response is grounded/cited.
5. **No overlap:** Given one learner turn, when routing completes, then the
   event trace contains exactly one next speaking role.
6. **Completion integrity:** Given a learner merely agrees, is silent, or gives
   an incorrect explanation, when assessment runs, then the session remains
   non-terminal. Completion requires both repair and explain-back pass.
7. **Instructor review:** Given a terminal session, when the summary is
   generated, then it records concept/scenario, role route, policy decisions,
   cited evidence references, outcome, and terminal reason.

## Error and safety behavior

| Condition | Required behavior |
| --- | --- |
| No authorized evidence | Abstain or redirect, record the reason, and do not invent a citation. |
| Prompt injection in source or learner text | Treat it as data; do not alter role, curriculum, or stopping rules. |
| Missing/invalid scenario metadata | Refuse session start and surface a configuration error. |
| Retrieval provider failure | Return a recoverable unavailable-evidence response; do not substitute model memory. |
| Duplicate learner request | Preserve idempotent event handling or mark the duplicate; never create concurrent role turns. |
| Unassessable explain-back | Request a more specific explanation; do not infer a pass. |

## Open decisions and approval gate

| Decision | Proposed direction | Why approval is needed |
| --- | --- | --- |
| Runtime/interface | Python backend API with a small web or CLI demonstration client | Determines repository layout and package tooling. |
| LLM and embeddings provider | Provider-neutral adapter, provider chosen by team | Affects cost, credentials, Vietnamese quality, and deployment. |
| Retrieval store | Local development implementation first; persistent store selected later | Affects dependencies and reproducibility. |
| Assessment policy | Instructor-configured rubric with recorded evidence | Defines the learning-pass contract. |
| Source corpus | One licensed/exported VLearn lesson plus a prepared scenario | Required before any grounding claim can be tested. |

No code should claim working retrieval, citations, or model behavior until the
team supplies the source corpus and approves ADR 0001.
