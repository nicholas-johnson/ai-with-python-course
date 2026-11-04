# Module 11 — Evals

> You cannot improve what you cannot measure. A Pathfinder agent that *seems* helpful in a live demo can still call the wrong tool, retrieve the wrong log, or invent a warp-core temperature that never appeared in the sources. This module builds an evaluation stack: deterministic golden tests for agents, retrieval metrics for RAG, an LLM-as-judge for generation quality, a faithfulness check for hallucinations, and a scorecard that picks a winner and gates a release.

## Learning goals

- Catch agent regressions with **golden tests**: a frozen reference, exact-match tool calls, and a judged answer averaged into one score.
- Score retrieval with **recall@k**, **precision@k**, and **MRR** against a labelled query set.
- Grade answers with an **LLM-as-judge** on correctness, completeness, and relevance.
- Measure **faithfulness**: every claim in an answer must be grounded in retrieved context.
- Compare two configs on a **scorecard** and **fail a release** that drops below a threshold.

---

## Why eval

A live chat is a sample of size one. Production systems need a frozen test set you can re-run after every prompt, chunking, or model change.

| Layer | Question it answers | Typical method |
| ----- | ------------------- | -------------- |
| Agent behaviour | Did it call the right tools with the right args? | Golden tests against a frozen reference |
| Retrieval | Did we fetch the right documents? | Recall@k, precision@k, MRR |
| Generation | Is the answer correct, complete, relevant? | LLM-as-judge |
| Grounding | Did it invent facts not in the sources? | Faithfulness / claim support |
| Release | Is this config better, and is it good enough? | Scorecard + gate |

Use cheap, deterministic checks (golden tests, retrieval metrics) in CI on every commit. Spend tokens on LLM-as-judge and faithfulness when you change prompts or retrieval, not on every keystroke.

---

## Golden-file testing

A **golden test** freezes a known-good outcome for a question — the tool calls and the answer you accept as correct — and re-checks a later run against it. The golden file holds *only* the question and the accepted outcome. What the agent does comes from the build under test, so when the agent changes, the suite says so.

That separation is the whole trick. If the fixture also scripts the agent's behaviour, the test just confirms the script matched itself and passes forever. Keep the reference and the behaviour apart and a real regression — "the agent stopped calling `get_ship_status`" — turns into a failing case.

```python
actual = run_case(client, question)        # what the build actually did
score = score_case(actual, case, judge)    # vs the frozen reference
# {"id": "warp-status", "score": 0.25, "passed": False,
#  "criteria": {"tools": 0.0, "correctness": 0.25,
#               "completeness": 0.0, "relevance": 0.75}}
#   expected  get_ship_status(system=warp)
#   actual    (no tools called)
```

Tool calls are structured, so they exact-match cleanly: 0 or 1. Prose does not: "Commander Elara Voss is the captain." and "The captain is Commander Elara Voss." are the same answer and a string comparison fails one of them. So exact-match the tools, and send the answer to an **LLM-as-judge** (below) for correctness, completeness and relevance.

That makes a case score continuous rather than pass/fail, and the suite a mean of means — average the criteria for a per-case score, average those for the suite:

```
suite = mean over cases of ( mean over criteria of s ),   s ∈ [0, 1]
```

Equal weights give a plain mean; the scorecard at the end of this module swaps the `1/M` for weights that sum to 1. A case passes when its score clears a threshold, so the floor is a knob rather than a string comparison.

The demo simulates both the build under test and the judge, so it runs with no key: build A matches the reference and scores 1.00, build B has had its prompt changed and scores 0.52. Point the same loop at a real client and nothing about the test changes — only the cost. Run the structured checks often; spend tokens on the judged pass when prompts or retrieval change.

---

## Retrieval metrics

You need a labelled set: for each query, the document IDs that *should* come back.

- **Recall@k** — of all relevant docs, what fraction appear in the top *k*? High recall means you did not miss the evidence.
- **Precision@k** — of the top *k* results, what fraction are relevant? High precision means less junk in the prompt.
- **MRR** (mean reciprocal rank) — `1 / rank` of the *first* relevant doc. Rewards putting a good hit near the top.

```python
recall_at_k(["LOG-002", "LOG-007", "LOG-011"], relevant=["LOG-002", "LOG-011"], k=3)  # 1.0
precision_at_k(["LOG-002", "LOG-007", "LOG-011"], relevant=["LOG-002", "LOG-011"], k=3)  # 2/3
mrr(["LOG-007", "LOG-002"], relevant=["LOG-002", "LOG-011"])  # 0.5
```

---

## LLM-as-judge

Word-overlap metrics (BLEU, ROUGE) punish paraphrase. A judge model reads the question, the candidate answer, and a reference, then scores 1–5 on:

- **Correctness** — are the facts accurate?
- **Completeness** — does it cover the key points in the reference?
- **Relevance** — does it address the question?

Get the scores back with structured outputs (a `JudgeScores` Pydantic model with `Field(ge=1, le=5)`), so there are no fences to strip or keys to guess, and average across a set of 20–100 triples. Temperature 0. Judge bias is real — use a rubric, multiple dimensions, and treat scores as *relative* (config A vs B) more than absolute truth.

---

## Faithfulness

A correct-sounding answer can still be ungrounded. Faithfulness splits the answer into claims and checks each one against the retrieved context (not against a gold answer).

```
faithfulness = supported_claims / total_claims
```

An answer that restates the sources scores 1.0. An answer that adds "the core is at 9000K" when the log says 94% efficiency scores lower. This is the generation-side cousin of citation verification (Module 13).

---

## Scorecard and gate

Run the same questions through two pipelines (plain RAG vs RAG + rerank). Build one scorecard per config, pick a winner on a metric, and **gate** a release: fail if recall, judge average, or faithfulness drops below a floor.

```python
gate(scorecard, {"avg_recall": 0.6, "overall": 0.5})
# {"passed": False, "failures": [{"metric": "avg_recall", "value": 0.4, "threshold": 0.6}]}
```

The Module 12 capstones (`exercises/04`–`07`) can reuse this as a release check, not a slide.

---

## Summary

- **Golden tests freeze the outcome.** The fixture does not script the agent. Exact-match the tool calls; judge the prose. Average the criteria for a case score, average those for the suite, and pass on a threshold. Cheap checks on every commit; judged passes when prompts or retrieval change.
- **Retrieval has numbers.** recall@k, precision@k, and MRR, on a small set you labelled properly.
- **Judge the answer, then check the claims.** Correctness, completeness, and relevance — then faithfulness against the retrieved context. Read the mismatches, not only the average.
- **Compare on a delta, gate on a floor.** “Did we get better?” is a different question from “is this shippable?”

---

## Demos

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python module-11-evals/demo/demo.py

# Option B - uv (no activation needed):
uv run python module-11-evals/demo/demo.py
```

Menu, no API key. `a` runs all five:

1. **Golden tests** — two agent builds against one frozen reference; the drifted build scores 0.52 and fails
2. **Retrieval metrics** — recall@k, precision@k, MRR on labelled ship-log queries
3. **LLM-as-judge** — canned judge JSON, dataset summary
4. **Faithfulness** — claims vs context, supported ratio
5. **Scorecard + gate** — RAG vs RAG+rerank, winner and release floor

## Exercises

The exercises chain: each one adds a measurement the next one can consume.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-golden-tests`](exercises/01-golden-tests/) | Agent-loop regression test with a mock LLM; exact-match tools, judge the prose, average into one score |
| [`exercises/02-retrieval-metrics`](exercises/02-retrieval-metrics/) | recall@k, precision@k, MRR on labelled ship-log queries |
| [`exercises/03-llm-judge`](exercises/03-llm-judge/) | LLM-as-judge: correctness, completeness, relevance |
| [`exercises/04-faithfulness`](exercises/04-faithfulness/) | Claim extraction + support check + faithfulness ratio |
| [`exercises/05-eval-compare`](exercises/05-eval-compare/) | Scorecard two configs, pick a winner, gate a release |

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-11-evals/ -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-11-evals/ -v
```

## Slides

From repo root: `pnpm slides:11`, or `cd module-11-evals/slides && pnpm dev`.

## Reference

- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al. 2023)](https://arxiv.org/abs/2306.05685)
- [FActScore: Fine-grained Atomic Evaluation of Factual Precision (Min et al. 2023)](https://arxiv.org/abs/2305.14251)
- [Evaluating Retrieval Quality (TREC / IR textbooks)](https://trec.nist.gov/) — precision, recall, MRR
- [RAGAS](https://docs.ragas.io/) — faithfulness, answer relevancy, context precision as a packaged library
- Golden-file agent tests — Module 2 demo pattern, promoted to a graded lab here
