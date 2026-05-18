# Exercise 03 — Debate + Consensus

## Recap on debate and consensus patterns

When a single agent might hallucinate or miss edge cases, you can improve reliability by adding **adversarial validation** or **ensemble voting**.

**Debate** pits two agents against each other — an advocate argues FOR a position while a skeptic argues AGAINST. After multiple rounds of back-and-forth, a neutral judge picks the stronger argument. This surfaces flaws that a single pass would miss:

```
Question → Advocate (FOR) ↔ Skeptic (AGAINST) → Judge → Winner
```

**Consensus voting** asks multiple independent agents the same question, then tallies which answer is best. This is analogous to ensemble methods in ML — individual agents may err, but the majority tends toward correctness:

```
Question → [Agent₁, Agent₂, Agent₃] → Vote → Winner
```

Both patterns combine naturally with the supervisor-critic pipeline from Exercise 02 — run the supervised query first, then validate the result through debate or voting.

## What you build

A multi-resolution system in **`start.py`** that provides three strategies for answering questions:

| Function | Description |
|---|---|
| `debate` | Structured N-round debate between advocate and skeptic |
| `judge` | LLM picks a winner from the final debate arguments |
| `consensus_vote` | Each specialist answers independently; majority vote picks the best |
| `multi_agent_answer` | Supervisor pipeline + debate validation combined |

The exercise imports `specialist_agent` from `agents.py` (Exercise 01) and `run_supervised_query` from `supervisor.py` (Exercise 02).

## Step-by-step

### 1. Implement `debate`

Set up two agents with opposing system prompts:
- **Advocate**: argues FOR the proposed action, cites benefits, counters objections
- **Skeptic**: argues AGAINST, identifies risks, flaws, and consequences

For each round:
1. Build the advocate's user message (round 1: the question; later rounds: the skeptic's last response)
2. Call the LLM and store the advocate's argument
3. Build the skeptic's user message (includes the advocate's current argument)
4. Call the LLM and store the skeptic's argument
5. Append `{"round": N, "advocate": str, "skeptic": str}` to the log

Maintain separate message histories so each agent accumulates context across rounds.

### 2. Implement `judge`

Call the LLM with JSON mode to evaluate both final arguments:
- System prompt: impartial judge, pick the stronger case
- User prompt: the question + both arguments
- Parse response for `{"winner": "advocate"|"skeptic", "reasoning": "..."}`
- Default to `"advocate"` if parsing fails

### 3. Implement `consensus_vote`

1. Call `specialist_agent` for each department in `DEPARTMENTS` to collect independent answers
2. Format all responses into a text block
3. For each department, ask a voting LLM (JSON mode) which response is best
4. Tally votes and return the winner with the highest count

### 4. Implement `multi_agent_answer`

Combine the supervisor pipeline with debate validation:
1. Call `run_supervised_query` to get the baseline answer
2. Construct a debate question around that answer (e.g. "Is this a good answer?")
3. Run `debate()` on the constructed question
4. Extract the final arguments and call `judge()`
5. Return all three pieces: supervised result, debate log, and judgment

## Try it

```bash
cd module-09-multi-agent/exercises/03-consensus
python start.py
```

Example commands:
- `/debate Should we lift the quarantine on Deck 7?` — run a standalone debate
- `/vote Should we hail the unknown vessel or raise shields?` — consensus vote across all specialists
- `/mode debate` then ask a question — uses the full supervisor + debate pipeline
- `/mode vote` then ask a question — uses consensus voting
- `quit` — exit

## Tests

```bash
pytest test_start.py -v
```

The tests verify:
- `debate` returns a list of round dicts with `advocate` and `skeptic` keys
- `debate` respects the `rounds` parameter (produces exactly N entries)
- `judge` returns a dict with `winner` and `reasoning`
- `judge` defaults gracefully on bad JSON
- `consensus_vote` returns the correct structure with responses, winner, and votes
- All tests use mocked OpenAI clients — no real API calls

## Stretch goals

- Add a "devil's advocate" mode where the skeptic always takes the opposite of the supervised answer
- Implement weighted voting where the critic's confidence score influences vote weight
- Add a timeout so debates can terminate early if both sides converge
- Track debate history across multiple questions to identify recurring disagreements
