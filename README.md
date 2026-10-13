# MASCOT

**M**ulti-**A**gent **S**imulated **C**lassroom for **O**nline **T**utoring

MASCOT is a group-project MVP for active learning from VLearn lesson material.
Rather than only answering questions, it simulates a small online classroom:
the learner identifies and corrects a Peer Student's common misconception,
receives Socratic guidance from a Teaching Assistant (TA), and can be escalated
to a Lecturer for deeper clarification. The session completes only when the
learner repairs the misconception and successfully explains the concept back.

## MVP goals

- Ground factual teaching claims in permitted lesson transcripts or slides.
- Attach inspectable citations to grounded instructional responses.
- Restrict retrieval to current and prerequisite lessons; redirect or refuse
  future and out-of-scope requests.
- Enforce distinct Peer Student, TA, and Lecturer behaviors with one authorized
  speaking role per learner turn.
- Record session events and create a concise instructor-facing learning
  summary.

## Proposed learning flow

```text
Peer Student misconception → learner correction attempt
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
              sufficient repair              needs support
                   │                             │
         explain-back assessment          TA Socratic hint
                   │                             │
                pass → complete       named escalation → Lecturer
```

All instructional routes are subject to the curriculum gate and evidence
retrieval. If MASCOT lacks permitted evidence, it abstains or redirects instead
of inventing an answer or citation.

## Roles

| Role | Responsibility |
| --- | --- |
| Learner | Correct the misconception and give an explain-back. |
| Peer Student | Present the instructor-configured common misconception. |
| Teaching Assistant | Ask Socratic questions and offer graduated hints without immediately supplying the answer. |
| Lecturer | Provide deeper clarification after an explicit escalation condition. |
| Orchestrator | Control turns, retrieval policy, state transitions, and stopping conditions. |

## Repository status

The project currently contains its working harness and proposed MVP
specification; no application code, dependency manifest, runtime, provider,
or lesson corpus has been selected yet. Consequently, there is no install,
run, test, or deployment command at this stage.

Before bootstrapping the application, the team must approve the architecture
proposal and provide:

1. One permitted VLearn lesson, concept, and misconception scenario.
2. The target demonstration interface (web or CLI).
3. An LLM/embedding provider and budget boundary.

## Documentation

- [MVP product specification](docs/product-spec.md): scope, roles, state,
  acceptance criteria, safety behavior, and open decisions.
- [ADR 0001](docs/adr/0001-mvp-architecture.md): proposed backend-first,
  policy-gated, provider-neutral architecture.
- [Repository guide](AGENTS.md): durable product rules and evidence
  expectations.
- [MASCOT orchestration skill](.codex/skills/mascot-orchestration/SKILL.md):
  workflow for feature work, evaluations, and major reviews.

## Contributing

Keep changes aligned with the MVP specification. Any implementation affecting
retrieval, citations, role routing, explain-back, or session completion must
include evidence for the corresponding acceptance criteria and must not claim
behavior that has not been implemented and verified.

## License

No license has been selected. Do not reuse course materials, source transcripts,
or generated artifacts outside the permissions granted to the project team.
