# ADR 0001: Backend-first, policy-gated MASCOT MVP

**Status:** proposed
**Date:** 2026-10-13
**Owner:** MASCOT project team
**Related specification:** [MVP product specification](../product-spec.md)

## Context

MASCOT needs to demonstrate multi-agent teaching over one lesson/concept while
preventing future-curriculum leakage, unsupported factual claims, agent-turn
overlap, and false learning-completion signals. The proposal requires
LangGraph-based orchestration but does not choose a language, web framework,
model provider, embedding provider, vector store, or hosting environment.

The repository contains no source, dependency manifest, test suite, or runtime
configuration. The project is therefore classified as **S1 planned single
application**: a small team and one MVP deployable, but with educational data
and behavior that require explicit boundaries. No stack-specific rule files
are present, so this ADR does not represent a selected implementation stack.

## Decision

After approval, bootstrap one modular, backend-first application with these
logical boundaries:

```text
client/demo → application API → session orchestrator (LangGraph)
                                  ├─ curriculum authorization
                                  ├─ retrieval adapter
                                  ├─ role policy / response adapter
                                  ├─ explain-back assessment
                                  └─ event log + summary projection
```

The orchestrator is the sole writer of session state and the sole component
that chooses the next role. Curriculum authorization runs before retrieval
results are supplied to a response-producing role. Response generation and
assessment are accessed through provider-neutral interfaces so the team can
select an LLM/embedding provider after evaluating cost and Vietnamese support.

For the first executable slice, use a local development persistence strategy
and fixture-based lesson/scenario data. The exact framework, package manager,
stores, and client technology remain deliberately unselected until approval.

## Alternatives considered

| Alternative | Rejected / deferred because |
| --- | --- |
| Single prompt with all roles | Cannot reliably enforce turn ownership, escalation, or inspectable terminal logic. |
| Give each agent an independent retriever | Makes curriculum policy and citation evidence harder to audit consistently. |
| Build a full LMS/multi-service platform | Exceeds the one-concept MVP and adds operations without validating pedagogy. |
| Select a provider/framework now | The team has not supplied budget, credentials, hosting, or source-corpus constraints. |

## Consequences and trade-offs

- The policy/orchestrator boundary adds interfaces and tests before a polished
  chat UI, but makes the required safeguards testable.
- Provider neutrality postpones lock-in, but the first implementation has
  adapter work and may initially use deterministic fixtures.
- A local-first MVP reduces setup burden, but is not a production security or
  multi-user deployment design.
- The event trail supports instructor review, but must minimize personal data
  and avoid secrets in logs.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Poorly prepared lesson metadata leaks future content | Validate metadata at ingestion and test authorization before generation. |
| Model produces convincing unsupported content | Require evidence/citation validation and abstain when evidence is inadequate. |
| Explain-back assessment is overly permissive | Use an instructor-configured rubric and preserve assessment evidence for review. |
| Source export or licensing is unavailable | Use only team-authorized materials/fixtures; do not present the MVP as VLearn-integrated. |

## Approval gate

The team must approve this ADR and provide a named lesson/concept, a permitted
source corpus, a target demo interface, and an LLM/provider budget boundary
before scaffolding the application. Approval authorizes a follow-up ADR that
selects the concrete Python/runtime, interface, storage, and model adapters.

## Revisit / rollback trigger

Supersede this decision if the project expands beyond one concept, needs
multi-user persistence or authentication, processes identifiable learner data,
or cannot meet curriculum/citation acceptance checks with a single modular
application.
