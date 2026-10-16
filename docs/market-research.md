# Market Research and Benchmark Analysis for MASCOT

## 1. Executive Summary

The objective of this document is to evaluate the existing market landscape and academic state-of-the-art (SOTA) in AI-driven tutoring, Socratic dialog systems, and multi-agent simulated classrooms. By analyzing current commercial platforms and research prototypes, we identify industry gaps and synthesize the **essential core standards** that the **MASCOT (Multi-Agent Simulated Classroom for Online Tutoring)** MVP must achieve.

Unlike conventional 1-on-1 AI tutors that merely answer questions or act as passive conversational partners, MASCOT combines:
1. **Multi-Agent Classroom Simulation** (Peer Student, Teaching Assistant, Lecturer).
2. **Cognitive Conflict Induction** (Peer expressing realistic misconceptions).
3. **Active Learning via the Protégé Effect & Feynman Technique** (Learner corrects the peer and provides an explain-back).
4. **Policy-Gated Retrieval-Augmented Generation (RAG)** (Strict curriculum boundaries and resolvable citations).

---

## 2. Competitive Landscape & Platform Survey

We surveyed five prominent platforms and research frameworks operating in the automated tutoring and classroom simulation domain:

### 2.1. Khanmigo (Khan Academy)
* **Overview:** A leading commercial AI tutor developed in collaboration with OpenAI, designed to serve as a personal Socratic guide for K-12 and higher education students.
* **Key Capabilities:**
  * Uses Socratic scaffolding: guides students step-by-step rather than immediately outputting answers.
  * Context-aware prompts tied to Khan Academy video exercises and problem sets.
* **Limitations & Gaps:**
  * **Isolated 1-on-1 paradigm:** Lacks social learning dynamics and peer interaction.
  * **Sycophancy vulnerability:** LLMs in 1-on-1 settings often succumb to user pressure, giving away hints too quickly or validating flawed reasoning.
  * **Passive validation:** Relies heavily on multiple-choice selection or math-step validation rather than requiring students to synthesize and teach concepts back.

### 2.2. CS50 AI Duck Debugger (Harvard University)
* **Overview:** An AI teaching assistant deployed across Harvard’s introductory CS50 course to support thousands of students globally.
* **Key Capabilities:**
  * Tuned to avoid writing code for students; instead, it highlights syntax/logic clues and asks diagnostic questions.
  * Grounded in official CS50 course notes, problem sets, and lecture transcripts.
* **Limitations & Gaps:**
  * Strictly a debugging/help-desk tool; it does not simulate an interactive classroom.
  * Does not induce cognitive dissonance (the student must initiate contact with an existing problem).
  * No explicit evaluation of the student's conceptual mastery before closing a thread.

### 2.3. OpenMAIC / SimClass (Academic Multi-Agent Classrooms)
* **Overview:** Academic research frameworks exploring LLM-based multi-agent interactive classrooms where AI instructors, teaching assistants, and multiple AI students coexist.
* **Key Capabilities:**
  * Demonstrates how agent-to-agent interactions enrich the classroom atmosphere.
  * Models social dynamics: simulated students raise hands, ask naive questions, and exhibit diverse personalities.
* **Limitations & Gaps:**
  * Focuses primarily on simulation and immersion rather than rigorous individual pedagogical assessment.
  * Turn-taking can become noisy and unpredictable without deterministic orchestration.
  * Lacks formal curriculum gating and verifiable completion criteria (e.g., verifying misconception repair).

### 2.4. Teachable Agents & The Protégé Effect (Betty’s Brain / Vanderbilt)
* **Overview:** Foundational educational research where students learn by teaching an artificial agent ("Betty").
* **Key Capabilities:**
  * Harnesses the **Protégé Effect**: students invest higher cognitive effort and gain deeper retention when responsible for correcting and teaching a peer.
  * Forces externalization of mental models through concept maps and corrective feedback.
* **Limitations & Gaps:**
  * Classical systems relied on rigid, rule-based reasoning engines and fixed graphical representations rather than flexible natural language.
  * Difficult to scale across diverse course materials without manual expert modeling.

### 2.5. Duolingo Max ("Explain My Answer" & Roleplay)
* **Overview:** Commercial conversational AI integrated into language learning.
* **Key Capabilities:**
  * Provides contextual explanations when a learner makes an error.
  * Interactive roleplay scenarios that evaluate conversational fluency.
* **Limitations & Gaps:**
  * Transactional feedback rather than sustained Socratic discovery.
  * Content is bite-sized; not designed for complex conceptual domains (e.g., computer science, engineering, or higher-ed STEM).

---

## 3. Comparative Benchmarking Matrix

| Feature / Dimension | Khanmigo | CS50 Duck | OpenMAIC | Betty's Brain | **MASCOT (Target)** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Social Classroom Simulation** | ❌ (1-on-1) | ❌ (1-on-1) | ✅ (Multi-agent) | ⚠️ (Agent only) | ✅ **Multi-Agent (Peer, TA, Lecturer)** |
| **Active Misconception Repair** | ❌ | ❌ | ⚠️ (Incidental) | ✅ (Core) | ✅ **Instructor-configured Misconception** |
| **Socratic Scaffolding (No direct answers)** | ✅ | ✅ | ⚠️ (Mixed) | ❌ | ✅ **Graduated Hints & Socratic Questions** |
| **Feynman Explain-Back Verification** | ❌ | ❌ | ❌ | ⚠️ (Concept map) | ✅ **Mandatory Semantic Explain-Back** |
| **Curriculum Scope Gating** | ⚠️ (Soft prompt) | ⚠️ (Context limit) | ❌ | ❌ | ✅ **Deterministic Gate (Prereq/Current only)** |
| **Resolvable Source Citations** | ⚠️ | ✅ | ❌ | ❌ | ✅ **Strict Source Location Citations** |
| **Deterministic Turn-Taking State Machine** | ❌ | ❌ | ⚠️ (Stochastic) | N/A | ✅ **LangGraph-driven Orchestration** |

---

## 4. Core Product Standards for MASCOT

Derived from market gaps and educational literature, MASCOT must satisfy the following three core pillars of standards:

### 4.1. Pedagogical Standards
1. **Epistemic Agency & Anti-Sycophancy:**
   * The AI agents must never validate incorrect reasoning just to appease the learner.
   * Direct answers must be withheld by the Teaching Assistant (TA); guidance must proceed through phased, graduated Socratic hints.
2. **Cognitive Dissonance via Peer Misconception:**
   * Learning begins with a realistic, configured misconception voiced by a simulated classmate (Peer Student).
   * The learner is challenged to detect the flaw, overcoming the illusion of explanatory depth.
3. **Mandatory Explain-Back (Feynman Technique):**
   * A session must **never** terminate on simple agreement or multiple-choice selection.
   * Completion requires: (a) successful repair of the peer's misconception, and (b) an accurate, self-generated explanation evaluated against an instructor rubric.

### 4.2. Retrieval & Grounding Standards (RAG Guardrails)
1. **Curriculum Gating:**
   * The retriever must explicitly filter chunks by `lesson_order` and `course_id`.
   * Future lessons or out-of-scope concepts must be rejected or redirected, preventing curriculum leakage.
2. **Inspectable Citations:**
   * Factual teaching assertions must be anchored to permitted transcript/slide segments, returning metadata (`source_id`, `source_location`).
3. **Abstain/Redirect Policy:**
   * If permitted sources lack sufficient grounding evidence, the system must abstain or redirect rather than hallucinate answers.

### 4.3. Architectural & Orchestration Standards
1. **Deterministic Single Speaking Role per Turn:**
   * An orchestrator (implemented via LangGraph) must strictly enforce that exactly one agent speaks per learner turn, eliminating chaotic agent cross-talk.
2. **Explicit Escalation Paths:**
   * Escalation from TA hints to Lecturer clarification must follow transparent, configured rules (e.g., maximum hint exhaustion).
3. **Auditable Event Logging & Instructor Summary:**
   * The system must record append-only state transitions, retrieval decisions, and rubric assessment results, compiling an actionable post-session summary for instructors without logging sensitive user data or API keys.

---

## 5. Strategic Implications & Recommended Next Steps

To move from specification to an executable minimum viable product:

1. **Select a Target Concept & Scenario (Milestone 1):**
   * Choose one concrete concept from a university lecture (e.g., *Object-Oriented Programming: Overloading vs. Overriding* or *Operating Systems: Virtual Memory & Page Replacement*).
   * Define the specific Peer Student misconception and an explain-back grading rubric.
2. **Bootstrap the Architecture (Milestone 2):**
   * Initialize a Python 3.10 virtual environment and dependency baseline (`langgraph`, `langchain-core`, model provider SDK).
   * Build the project using a modular structure: `core/`, `retrieval/`, `agents/`, `evaluators/`, and `cli/`.
3. **Implement Retrieval & Curriculum Filter (Milestone 3):**
   * Load the prepared lecture data into structured chunks carrying lesson order metadata.
   * Verify that out-of-scope queries are blocked before reaching LLM generation.
4. **Develop Orchestration Graph & Automated Verification (Milestone 4):**
   * Construct the LangGraph state machine linking Peer, TA, Lecturer, and Evaluator nodes.
   * Implement automated `pytest` test suites validating the acceptance criteria outlined in `product-spec.md`.

