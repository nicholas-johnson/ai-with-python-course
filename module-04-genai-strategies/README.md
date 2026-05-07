# Module 4 — Conversational AI + Multimodal

**Time to build something real.** This module pulls together the agent core, LLM integration, and prompt engineering into a working conversational AI application. You will apply prompt engineering techniques, work with multimodal inputs (vision, audio), reason about model selection, and add guardrails that make the system production-ready.

## Learning goals

- Build a **conversational AI application** that integrates the agent core, LLM calls, and prompt engineering from earlier modules.
- Apply **prompt engineering**: system prompts, few-shot examples, structured outputs, and grounding.
- Work with **multimodal** inputs and outputs: vision/image analysis, speech-to-text, text-to-speech.
- Add **guardrails**: model selection, token budgeting, content filters, and confidence thresholds.

## Topics

- Prompt engineering: system prompts, few-shot patterns, structured outputs, grounding.
- Multimodal APIs: sending images for analysis, speech-to-text (Whisper), text-to-speech.
- Model selection trade-offs: quality, cost, latency.
- Token counting, truncation, and budget enforcement.
- Guardrails: schema checks, content filters, confidence thresholds, eval harnesses.

## Demos

```bash
python module-04-genai-strategies/demo/01_prompting_patterns.py
python module-04-genai-strategies/demo/02_model_selection.py
python module-04-genai-strategies/demo/03_guardrails.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-structured-prompts`](exercises/01-structured-prompts/) | Build prompts that yield **JSON-parseable** outputs. |
| [`exercises/02-token-budget`](exercises/02-token-budget/) | **Count tokens** and enforce a max budget before calling the model. |
| [`exercises/03-guardrail-chain`](exercises/03-guardrail-chain/) | Chain **schema validation**, **content filter**, and **confidence** threshold. |

Run tests for this module:

```bash
pytest module-04-genai-strategies/
```

## Slides

From repo root: `pnpm slides:04`, or `cd module-04-genai-strategies/slides && pnpm dev`.

## Reference

- [OpenAI — Prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic — Prompting long context](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
- [tiktoken (OpenAI tokenizer)](https://github.com/openai/tiktoken)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
