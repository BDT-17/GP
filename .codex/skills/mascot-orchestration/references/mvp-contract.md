# MASCOT MVP Contract

## In scope

- One instructor-selected VLearn lesson and concept.
- A configured common misconception presented by a Peer Student role.
- A learner correction attempt, TA Socratic hints, and an explicit Lecturer
  escalation path.
- Retrieval grounded in lesson transcripts and/or slides, with inspectable
  citations.
- Curriculum-aware access controlled by course, lesson, concept, source, and
  lesson order metadata.
- Shared session state, deterministic turn ownership, stopping conditions,
  session logging, and an instructor-facing learning summary.
- A mandatory explain-back checkpoint after misconception repair.

## Out of scope unless explicitly approved

- Broad multi-course tutoring, automatic curriculum authoring, grading beyond
  the selected concept, learner profiling, or high-stakes educational claims.
- Retrieval of future lessons merely because they are present in an index.
- Direct-answer behavior from the TA when a Socratic hint can advance the
  learner.
- Treating generative confidence, a citation-looking string, or a learner's
  one-word agreement as proof of learning.

## Acceptance evidence

| Capability | Required observable evidence |
| --- | --- |
| Grounding | Factual response cites permitted transcript/slide material and the citation resolves to that material. |
| Curriculum control | Eligible content is retrievable; future/out-of-scope content produces a logged deny/redirect decision. |
| Role separation | Peer Student follows the scenario misconception, TA produces hints/questions, Lecturer activates only through its escalation condition. |
| Turn control | The event sequence identifies one authorized next speaker per learner turn. |
| Explain-back | Completion record contains a misconception repair and an assessment of a grounded learner explanation. |
| Observability | Session log and concise instructor summary capture retrieval, routing, outcomes, and terminal reason with minimized learner data. |

## Minimum scenario set

1. Learner correctly repairs the misconception and passes explain-back.
2. Learner struggles; TA uses one or more Socratic hints without disclosing the
   answer immediately.
3. Named escalation condition routes to Lecturer.
4. Future-lesson request is refused or redirected without retrieval leakage.
5. Out-of-scope question abstains or redirects because evidence is insufficient.
6. Prompt-injected or convincing unsupported claim does not bypass grounding,
   role rules, or citations.
7. One-word, silent, or incorrect learner response does not satisfy completion.
