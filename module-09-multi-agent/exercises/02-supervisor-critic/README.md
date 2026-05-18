# Exercise 02 — Supervisor-Critic Pipeline

## Recap

In Exercise 01 you built a router that dispatches queries to specialist agents. The specialist always gets one shot -- whatever it says goes straight to the user. That works for simple cases, but there's no quality gate.

A **supervisor-critic pipeline** adds a review loop. After the specialist responds, a **critic agent** evaluates the answer for accuracy, completeness, and hallucination. If the critic rejects the response, the specialist revises it -- incorporating the critic's feedback -- and the cycle repeats up to a configurable limit:

```
User query
  → Router (classify)
  → Specialist (respond)
  → Critic (review)
      ├─ approved  → return to user
      └─ rejected  → Specialist (revise with feedback) → Critic again …
```

The **supervisor** orchestrates this loop and records a **trace** of every agent interaction, so you can inspect exactly what happened at each step.

## What you build

A console app in **`start.py`** that layers a critic review loop on top of the Exercise 01 specialist agents. The specialist agents are imported from `agents.py` (provided).

**Key components:**

| Component | Description |
|---|---|
| `CriticAgent` | Reviews a specialist response via JSON mode, returns approved/rejected with feedback |
| `SupervisorAgent` | Orchestrates classify → specialist → critic loop with revision cap |
| `run_supervised_query` | Convenience function that creates a supervisor and runs a query |

## Step-by-step

### 1. Implement `CriticAgent.review`

The critic evaluates a specialist's response and returns structured feedback:

- Call `client.chat.completions.create` with `gpt-4o-mini` and JSON mode
- Use `CRITIC_PROMPT` as the system prompt
- The user message should include both the original query and the specialist's response so the critic has full context
- Parse the JSON response into `{"approved": bool, "feedback": str}`
- If JSON parsing fails, default to `approved=True` (fail open)

### 2. Implement `SupervisorAgent.run`

Wire together the full pipeline with a revision loop:

1. Classify the query using `classify_query` from `agents.py` -- add a trace entry
2. Get the specialist response using `specialist_agent` -- add a trace entry
3. Loop up to `max_revisions + 1` times:
   - Ask the critic to review -- add a trace entry
   - If approved, break out of the loop
   - Otherwise, call `_revise` to get an improved response -- add a trace entry
4. Return `{"department": str, "response": str, "trace": list}`

Each trace entry is a dict. Use an `"agent"` key to identify which agent acted (e.g. `"router"`, `"specialist"`, `"critic"`).

### 3. Implement `SupervisorAgent._revise`

Ask the specialist to revise its response using the critic's feedback:

- Look up the system prompt for the department from `SPECIALIST_PROMPTS`
- Build a message list that includes the original query, the previous response (as an assistant message), and the critic's feedback (as a follow-up user message)
- Return the revised response text

### 4. Implement `run_supervised_query`

A thin wrapper:

1. Create a `SupervisorAgent` with the given client and `max_revisions`
2. Call `supervisor.run(query)`
3. Return the result

### 5. Run the interactive loop

The `main()` function and command handling are already provided. Once you implement the core components, these commands will work:

| Command | Action |
|---|---|
| any text | Run through the supervised pipeline and show the response |
| `/trace` | Show the full agent trace from the last query |
| `/max-revisions N` | Set the revision cap (default 2) |
| `/agents` | List all agents in the team |
| `quit` | Exit |

## Try it

```bash
cd module-09-multi-agent/exercises/02-supervisor-critic
python start.py
```

Try queries and use `/trace` to see the full pipeline:

```
You: Crew radiation exposure levels?
[medical] (approved)
Agent: All crew members within safe limits. Deck 4 personnel at 12 mSv — monitoring advised.

You: /trace
[Agent Trace]
  1. {'agent': 'router', 'department': 'medical'}
  2. {'agent': 'specialist', 'department': 'medical', 'response': '...'}
  3. {'agent': 'critic', 'approved': True, 'feedback': 'Accurate and complete.'}

You: /max-revisions 0
[Max revisions set to 0]

You: Decrypt the signal
[comms] (max revisions reached)
Agent: ...
```

With `/max-revisions 0`, the critic still reviews but the specialist never gets a second chance.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `CriticAgent.review` returns a dict with `approved` (bool) and `feedback` (str)
- `CriticAgent.review` defaults to approved on bad JSON
- `SupervisorAgent.run` returns `department`, `response`, and `trace`
- When the critic approves first time, trace has exactly 3 entries (router, specialist, critic)
- When the critic rejects, trace includes revision entries
- `SupervisorAgent` respects `max_revisions` and doesn't loop forever
- `run_supervised_query` returns the same structure as `SupervisorAgent.run`
- No real OpenAI calls -- all tests use mocked clients

## Stretch goals

- Add a confidence score to the critic's review (e.g. `"confidence": 0.85`) and only reject below a threshold
- Implement a revision history: show the user all drafts, not just the final one
- Add a `/compare` command that runs the same query with and without the critic, so you can see the quality difference
