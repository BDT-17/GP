---
name: mascot-orchestration
description: Coordinate MASCOT multi-agent tutoring features, RAG/curriculum policy, evaluation, and implementation reviews. Use for work involving Peer Student, Teaching Assistant, Lecturer, lesson retrieval, citations, session state, explain-back, or instructor logs.
---

# MASCOT Orchestration

Build or assess a MASCOT capability using evidence from the configured lesson
materials and the current repository—not unstated assumptions.

## Inputs and outputs

Inputs: the requested outcome; lesson/concept/scenario identifiers when
available; relevant source, configuration, evaluation, and runtime files.

Outputs: a bounded implementation or decision; verification evidence; and a
short handoff containing changed paths, commands/results, retrieval-policy
coverage, and remaining risks. Put optional inspectable intermediate artifacts
under `_workspace/`; their absence never proves completion.

For every changed behavior, include an acceptance-evidence matrix in the
handoff. Each row must name the MVP-contract capability or scenario, its
expected policy/role/terminal outcome, the evidence source (test, log, fixture,
or manual trace), and the result. Mark unverified rows explicitly; do not fold
them into a broad claim of coverage.

Read `references/mvp-contract.md` for the MVP boundary and acceptance matrix.

## Routing and roles

Use direct execution for a localized change with a clear owner and existing
checks. For work crossing orchestration, retrieval, and evaluation, use a
producer-reviewer loop with at most two repair cycles.

The orchestrating Codex instance owns delegation, handoffs, and final
integration. Its role is one GPT-5.6 Sol Orchestrator. Assign only the minimum
independent work needed, with these role briefs:

- **Architecture/implementation reviewer (GPT-5.6 Terra):** trace state,
  retrieval boundaries, and role permissions; identify unsafe assumptions and
  implementation gaps. Do not broaden the product scope.
- **Security/adversarial reviewer (GPT-5.6 Terra):** challenge prompt
  injection, unsupported claims, citation bypass, future-content leakage,
  direct-answer leakage, and turn overlap. Report concrete reproduction paths
  and evidence.
- **Reconnaissance/test reviewer (GPT-5.6 Luna):** inventory actual files and
  commands; run bounded checks; map each observed result to an acceptance case.
  Do not approve product behavior from static prompts alone.

Each handoff must use this format:

```text
Scope:
Evidence inspected:
Findings / changed paths:
Verification and result:
Acceptance-evidence matrix (capability/scenario | expected outcome | evidence | result):
Open risks or missing evidence:
```

Independent read-only inspection and test design may run in parallel. Do not
implement or approve the final behavior until the retrieval policy, role state
machine, and success criteria are reconciled at a barrier.

## Required design checks

1. Identify the selected lesson, concept, misconception, curriculum order,
   source locations, and citation format. If they do not exist yet, record the
   gap and ask before fabricating learning content.
2. Make authorization data-driven: course, lesson, concept, source, and
   lesson-order metadata must determine eligibility before generation.
3. Keep a single session state authority for active role, learner attempt,
   hint/escalation count, retrieval evidence, misconception-repair status,
   explain-back assessment, and terminal reason.
4. Specify why the next role may speak. The Peer Student cannot silently become
   a tutor; the TA must use questions/hints; the Lecturer must enter through a
   named escalation rule.
5. Require citations for factual instructional claims. When adequate permitted
   evidence is absent, abstain or redirect with an explicit reason.
6. Evaluate adversarial and normal paths. At minimum cover each case listed in
   `AGENTS.md`; assert both the user-visible response and recorded policy/turn
   evidence.
7. Redact or minimize learner data in logs, and never put provider keys,
   tokens, or raw sensitive content in fixtures, prompts, or summaries.

## Review and repair loop

The producer supplies implementation plus targeted verification. The reviewer
checks it against the MVP contract and returns only actionable defects with
file/line or test evidence. Repair only validated defects, then rerun relevant
checks. After two cycles, preserve partial artifacts and report the missing
evidence rather than expanding scope or repeatedly retrying an external
mutation.

## Stop condition and final report

Stop when the requested bounded outcome is implemented or assessed, applicable
checks pass, and each changed behavior has evidence for role, curriculum,
citation, turn, and completion rules. Report:

1. delivered outcome and changed paths;
2. verified commands/results (or explicitly that no executable checks exist);
3. acceptance cases covered and their evidence;
4. known limits, missing inputs, and next decision required.

## Trigger examples

Use this skill for: “add curriculum-aware retrieval for the TA,” “review the
Lecturer escalation flow,” or “evaluate explain-back completion.”

Do not use this skill for: “rename a generic repository file” when it has no
effect on MASCOT behavior, curriculum data, evaluation, or documentation.
