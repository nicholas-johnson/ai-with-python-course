# Module 11 — Evals

> You cannot improve what you cannot measure. A Pathfinder agent that *seems* helpful in a live demo can still call the wrong tool, retrieve the wrong log, or invent a warp-core temperature that never appeared in the sources. This module builds an evaluation stack: deterministic golden tests for agents, retrieval metrics for RAG, an LLM-as-judge for generation quality, a faithfulness check for hallucinations, and a scorecard that picks a winner and gates a release.

## Learning goals

- Regression-test a tool-calling agent with **golden files** and a mock LLM (no API key, no flakiness).
- Score retrieval with **recall@k**, **precision@k**, and **MRR** against a labelled query set.
- Grade answers with an **LLM-as-judge** on correctness, completeness, and relevance.
- Measure **faithfulness**: every claim in an answer must be grounded in retrieved context.
- Compare two configs on a **scorecard** and **fail a release** that drops below a threshold.

---

## Why eval

A live chat is a sample of size one. Production systems need a frozen test set you can re-run after every prompt, chunking, or model change.

| Layer | Question it answers | Typical method |
| ----- | ------------------- | -------------- |
| Agent behaviour | Did it call the right tools with the right args? | Golden tests (mock LLM) |
| Retrieval | Did we fetch the right documents? | Recall@k, precision@k, MRR |
| Generation | Is the answer correct, complete, relevant? | LLM-as-judge |
| Grounding | Did it invent facts not in the sources? | Faithfulness / claim support |
| Release | Is this config better, and is it good enough? | Scorecard + gate |

Use cheap, deterministic checks (golden tests, retrieval metrics) in CI on every commit. Spend tokens on LLM-as-judge and faithfulness when you change prompts or retrieval, not on every keystroke.

---

## Golden-file testing

Mock the LLM with **scripted responses**. The agent loop still runs: it sees `tool_calls`, executes handlers, appends tool results, and reads the final `content`. You assert the tools and the answer.

Golden tests are fast (no network), free (no tokens), and deterministic (same result every run). They catch "the agent stopped calling `get_ship_status`" — not "the prose got slightly worse".

```python
actual = run_case(client, case)
# actual == {"tools": [{"name": "get_crew_count", "arguments": {"department": "engineering"}}],
#            "answer": "Engineering has 2 crew members."}
score = score_case(actual, case)  # {"passed": True, "mismatches": []}
```

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

Ask for JSON, parse defensively (strip markdown fences), and average across a set of 20–100 triples. Temperature 0. Judge bias is real — use a rubric, multiple dimensions, and treat scores as *relative* (config A vs B) more than absolute truth.

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

The capstone (Module 12) can reuse this as a release check, not a slide.

---

## Field rules

- **Mock for CI, live for exploration.** Golden tests and retrieval metrics belong in pytest. Judge and faithfulness cost tokens — run them on a schedule or on PR labels, not on every save.
- **Label a small set well.** Twenty queries with real relevant doc IDs beat two hundred guessed ones.
- **Never trust a single number.** Look at mismatches and unsupported claims, not only the average.
- **Gate on a floor, compare on a delta.** "Did we get worse?" is a different question from "which config wins?"

---

## Demos

```bash
python module-11-evals/demo/demo.py
```

Five parts, no API key — press Enter / pick a number:

1. **Golden tests** — scripted tool calls, pass/fail on a Pathfinder agent
2. **Retrieval metrics** — recall@k, precision@k, MRR on labelled ship-log queries
3. **LLM-as-judge** — canned judge JSON, dataset summary
4. **Faithfulness** — claims vs context, supported ratio
5. **Scorecard + gate** — RAG vs RAG+rerank, winner and release floor

## Exercises

The exercises chain: each one adds a measurement the next one can consume.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-golden-tests`](exercises/01-golden-tests/) | Mock-LLM agent loop, score tools + answer, run a golden suite |
| [`exercises/02-retrieval-metrics`](exercises/02-retrieval-metrics/) | recall@k, precision@k, MRR on labelled ship-log queries |
| [`exercises/03-llm-judge`](exercises/03-llm-judge/) | LLM-as-judge: correctness, completeness, relevance |
| [`exercises/04-faithfulness`](exercises/04-faithfulness/) | Claim extraction + support check + faithfulness ratio |
| [`exercises/05-eval-compare`](exercises/05-eval-compare/) | Scorecard two configs, pick a winner, gate a release |

```bash
pytest module-11-evals/ -v
```

## Slides

From repo root: `pnpm slides:11`, or `cd module-11-evals/slides && pnpm dev`.

## Reference

- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al. 2023)](https://arxiv.org/abs/2306.05685)
- [FActScore: Fine-grained Atomic Evaluation of Factual Precision (Min et al. 2023)](https://arxiv.org/abs/2305.14251)
- [Evaluating Retrieval Quality (TREC / IR textbooks)](https://trec.nist.gov/) — precision, recall, MRR
- [RAGAS](https://docs.ragas.io/) — faithfulness, answer relevancy, context precision as a packaged library
- Golden-file agent tests — Module 2 demo pattern, promoted to a graded lab here
