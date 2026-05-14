# Exercise 03 — Multi-Source QA

## Mission

The Pathfinder's knowledge is spread across vector stores, knowledge graphs, and keyword-indexed logs. Build a multi-source retrieval pipeline that fans out to all backends, merges results, and answers with ranked citations.

## Objectives

1. Implement `fan_out(query, backends) -> dict[str, list]` that queries every backend in parallel (simulated) and collects results keyed by backend name.
2. Implement `merge_and_rank(result_sets) -> list[SearchResult]` that deduplicates by `source_id` and sorts by score descending.
3. Implement `multi_source_qa(query, backends, llm_call) -> Answer` that ties fan-out, merge, and LLM answering together.

## Run

```bash
pytest module-10-adaptive-retrieval/exercises/03-multi-source-qa/test_start.py -v
```
