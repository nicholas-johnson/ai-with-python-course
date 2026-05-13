# Exercise 03 — Grounded QA

## Mission

The Pathfinder crew needs answers they can trust. Build a grounded question-answering function that queries the knowledge graph, retrieves supporting evidence, and returns answers with source citations and confidence scores.

## Objectives

1. Implement `retrieve_relevant(graph, question, top_k) -> list[dict]` that finds graph entities and relationships relevant to a question.
2. Implement `build_grounded_prompt(question, evidence) -> str` that constructs a prompt asking the LLM to answer with citations.
3. Implement `grounded_qa(question, graph, llm_call) -> GroundedAnswer` that ties retrieval, prompting, and parsing together.

## Constraints

- `GroundedAnswer` must include at least one `Citation` with a non-empty `source_id`.
- Confidence must be between 0 and 1.
- If no relevant evidence is found, return a `GroundedAnswer` with `confidence=0.0` and an answer indicating insufficient data.

## Run

```bash
pytest module-08-structured-facts/exercises/03-grounded-qa/test_start.py -v
```
