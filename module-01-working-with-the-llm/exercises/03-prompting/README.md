# Exercise 03 -- Prompt Engineering

> Write system prompts that make the LLM behave in specific ways -- personas, format constraints, guardrails, and few-shot patterns.

## Recap

Everything the model does starts with the **system prompt**. A good system prompt tells the model three things: **who** it is, **how** it should respond, and **what** it should refuse.

**Persona** prompts give the model a character and voice:

```python
"You are a pirate captain. Speak in exaggerated pirate slang. Never break character."
```

**Format constraints** control the shape of the output:

```python
"Always respond in bullet points starting with '- '. No introductory or closing text."
```

**Guardrails** define what the model should refuse:

```python
"You ONLY answer questions about astronomy. For anything else, say: 'I can only help with astronomy.'"
```

**Few-shot examples** teach the model a pattern by showing input/output pairs directly in the prompt:

```python
"""Classify ship events. Examples:

User: The engine overheated.
Assistant: ENGINEERING: Engine temperature exceeded safe limits.

User: Crew saw lights outside.
Assistant: OBSERVATION: Unidentified visual phenomenon reported.

Follow this format exactly: CATEGORY: one-line explanation."""
```

The key insight is that prompts are **instructions, not wishes**. Vague prompts get vague results. Specific, explicit prompts with clear rules and examples get consistent output.

## What you build

Six system prompts, each targeting a different prompting skill. The `run_prompt()` helper and interactive runner are already provided -- you only write the prompts.

| Function | Skill | Goal |
| -------- | ----- | ---- |
| `pirate_prompt()` | Persona / voice | AI talks like a pirate |
| `bullet_prompt()` | Format constraints | AI answers only in `- ` bullet points |
| `json_prompt()` | Structured output | AI responds with valid JSON containing an `"answer"` key |
| `haiku_prompt()` | Creative constraints | AI responds with exactly 3 lines (a haiku) |
| `refusal_prompt()` | Guardrails / scope | AI refuses off-topic questions, answers space/astronomy ones |
| `few_shot_prompt()` | Few-shot examples | AI classifies events as `CATEGORY: explanation` |

Study the `BASE_PROMPTS` dictionary in `start.py` first -- those are complete, working examples of different prompting techniques.

## Step-by-step

### 1. Implement `pirate_prompt() -> str`

Return a system prompt that makes the model talk like a pirate. Tell it who it is (a pirate), how it should speak (pirate slang -- "arr", "matey", "ye", "ahoy"), and that it should never break character.

Test it by asking about anything mundane -- the answer should be dripping with pirate flavour.

### 2. Implement `bullet_prompt() -> str`

Return a system prompt that forces bullet-point output. Be explicit: every line must start with `- `, and there should be no introductory or closing sentences. Tell the model what to include **and what not to include**.

### 3. Implement `json_prompt() -> str`

Return a system prompt that makes the model respond with raw JSON. Specify the schema (a JSON object with an `"answer"` key) and forbid markdown fences, explanations, or anything outside the JSON.

### 4. Implement `haiku_prompt() -> str`

Return a system prompt that produces exactly 3 lines (a haiku). State the format rule clearly and tell the model to skip any preamble, title, or trailing text.

### 5. Implement `refusal_prompt() -> str`

Return a system prompt that restricts the AI to space and astronomy topics. Define the scope, provide an explicit refusal message for off-topic questions, and make it clear the model should never answer outside its scope.

Test with both on-topic ("How far is Mars?") and off-topic ("How do I bake a cake?") questions.

### 6. Implement `few_shot_prompt() -> str`

Return a system prompt that includes 2-3 examples of the `CATEGORY: explanation` format. The examples teach the model the pattern. End with an instruction to follow the format exactly.

## Try it

```bash
python start.py
```

The interactive runner lets you pick any base prompt or challenge:

1. Type `base:classifier` to try the sentiment classifier base prompt.
2. Type a message like `"I love this ship!"` -- you should get `POSITIVE`.
3. Type `back` to return to the menu.
4. Type `pirate` to try your pirate challenge (once implemented).
5. Type any message and see if the AI responds in pirate speak.
6. Try each challenge with its suggested test message and with your own inputs.

## Tests

```bash
pytest module-01-working-with-the-llm/exercises/03-prompting/test_start.py -v
```

The structural tests (no API key needed) check that each function returns a non-empty string. The integration tests (require `OPENAI_API_KEY`) call the API and verify the output matches the expected format.

## Stretch goals

1. Write a `temperature_demo()` that calls the same prompt at `temperature=0.0` and `temperature=1.5` and compares the outputs.
2. Add a `chain_of_thought_prompt()` that asks the model to reason through a maths problem step by step before giving the final answer.
3. Try breaking your own `refusal_prompt` -- can you craft a user message that tricks the model into answering off-topic? Then harden the prompt to resist it.
