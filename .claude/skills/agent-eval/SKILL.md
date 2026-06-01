---
name: agent-eval
description: Evaluate and validate whether an AI agent or automation actually produces correct, reliable output. Use when the user wants to test an agent, build a "golden" test set, check for hallucinations, measure reliability, or regression-test after changing a prompt/model/knowledge base. Trigger phrases: "is this agent working", "validate", "test my agent", "evals", "did the change break anything".
---

# Evaluating an agent (the non-developer playbook)

Goal: prove an agent's output is correct *before* trusting it, and catch silent breakage when it changes. Output is a short eval plan + (where possible) a run against it. No coding required — this is methodology.

## Steps

1. **Define "correct" in writing.** Ask the user what a good output MUST contain and what counts as failure. For trading/finance work: the exact facts, numbers, or sources required. Refuse to evaluate against a vague goal — pin it down first.

2. **Build a golden test set (20–50 cases).** Each case = `question` + `expected source/context` + `expected answer`. Pull these from REAL past failures and real use, not invented examples. This is the answer key, reused on every change.

3. **Run the RAG Triad** (for any knowledge-base/RAG answer), scoring each separately:
   - **Context relevance** — did it retrieve the right documents?
   - **Groundedness** — is every claim supported by those documents (not invented)?
   - **Answer relevance** — did it answer the actual question?
   A failure in one tells you *where* it broke (retrieval vs. generation).

4. **Hallucination test.** Instruct the agent to say "I don't know / insufficient information," then deliberately ask out-of-scope questions. Confident invention instead of declining = fail.

5. **Read the transcript, not just the answer.** Inspect intermediate steps (searches, retrieved docs, tool calls). For multi-step agents, validate the *path*, not only the destination — a right answer reached by wrong reasoning will fail next time.

6. **Measure reliability, not one run.** Run each critical case ~10×. Report pass rate. Flag anything below ~95% on a step that gets chained — a 75%-per-step agent fails badly over a multi-step workflow (pass^k collapses fast).

7. **Pick graders deliberately:** code/exact-match for numbers & yes/no facts; LLM-as-a-judge (a second model grading against the rubric) for nuanced text; human review for high-stakes items. Use cheap automated checks broadly, reserve human review for what matters.

8. **Regression-test on every change.** Any prompt tweak, model swap, or knowledge-base edit → re-run the FULL golden set and diff scores vs. the previous version. Surface anything that regressed.

## Deliverable
A concise eval report: the "correct" definition, the test set (or a starter set), per-case pass/fail with which check failed, a reliability number, and a clear verdict + what to fix. Keep human-in-the-loop on anything irreversible.
