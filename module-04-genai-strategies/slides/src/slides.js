export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 4 — GenAI Strategies',
      subtitle: 'Model selection, multimodal, and guardrails',
      icon: 'sparkles',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'What this module covers',
      icon: 'compass',
      points: [
        'Build a **Research Assistant** web app — streaming chat, tool use, vision, and audio.',
        'Model selection: choosing the right model for **quality, cost, and latency**.',
        'Multimodal: **vision**/image analysis, **speech-to-text** (Whisper), text-to-speech.',
        'Guardrails: schema validation, content filters, and **confidence thresholds**.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Build a **FastAPI app** with SSE streaming chat and tool integration.',
        'Connect an **MCP server** to a web API for real-time tool use.',
        'Count tokens, enforce **budgets**, and truncate context gracefully.',
        'Work with **multimodal** inputs: images (GPT-4o), audio (Whisper).',
        'Chain **guardrails**: schema check → content filter → confidence gate.',
      ],
    },
  },

  // ---- Section: Model selection + tokens ----
  {
    type: 'title',
    content: {
      title: 'Model selection + tokens',
      subtitle: 'Choosing the right model and managing budgets',
      icon: 'scale',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Model selection trade-offs',
      icon: 'scale',
      points: [
        '**Quality**: GPT-4o for hard reasoning; GPT-4o-mini for simple classification.',
        '**Cost**: 10-50x price difference between tiers — measure before committing.',
        '**Latency**: smaller models respond faster; streaming helps perception.',
        '**Context window**: 128k tokens is huge but costs scale linearly.',
        'Rule of thumb: start with the cheapest model that passes your eval suite.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Token counting and budgets',
      code: `import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")

def count_tokens(text: str) -> int:
    return len(enc.encode(text))

def enforce_budget(messages, max_tokens):
    """Drop oldest user turns until under budget."""
    total = sum(count_tokens(m["content"]) for m in messages)
    while total > max_tokens and len(messages) > 2:
        removed = messages.pop(1)  # keep system prompt
        total -= count_tokens(removed["content"])
    return messages`,
      highlights: [
        'tiktoken gives exact counts for OpenAI models',
        'Always preserve the system prompt — it sets behaviour',
      ],
    },
  },
  // ---- Demo: Model selection ----
  {
    type: 'title',
    content: {
      title: 'Demo — Model selection',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 1',
      icon: 'rocket',
    },
  },

  // ---- Section: Multimodal + guardrails ----
  {
    type: 'title',
    content: {
      title: 'Multimodal + guardrails',
      subtitle: 'Vision, audio, and defence in depth',
      icon: 'shield',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Multimodal inputs',
      icon: 'image',
      points: [
        '**Vision**: send images as base64 or URL in user messages.',
        '**Audio input**: Whisper API transcribes speech to text.',
        '**Audio output**: TTS API generates spoken responses.',
        'Same message format — just different content types.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Vision — image analysis',
      code: `response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe what you see in this image."},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{img_b64}"
            }},
        ],
    }],
)`,
      highlights: [
        'Content is a list of parts — text and images mixed freely',
        'Works with base64 data URIs or public HTTPS URLs',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Guardrails — defence in depth',
      icon: 'shield',
      points: [
        '**Schema validation**: does the response parse into the expected shape?',
        '**Content filter**: block or flag toxic, off-topic, or hallucinated content.',
        '**Confidence threshold**: reject low-confidence answers with a fallback.',
        '**Chain them**: schema → filter → confidence, in order. Fail early.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Guardrail chain',
      code: `def run_guardrails(response, schema, blocked_terms, min_confidence):
    # Step 1: Schema check
    try:
        data = schema.model_validate_json(response)
    except ValidationError as e:
        return GuardrailResult(passed=False, reason=f"Schema: {e}")

    # Step 2: Content filter
    for term in blocked_terms:
        if term.lower() in response.lower():
            return GuardrailResult(passed=False, reason=f"Blocked: {term}")

    # Step 3: Confidence gate
    if data.confidence < min_confidence:
        return GuardrailResult(passed=False, reason="Low confidence")

    return GuardrailResult(passed=True, data=data)`,
      highlights: [
        'Each guardrail returns early on failure — no wasted work',
        'Structured result lets the caller decide what to do next',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Unguarded vs guarded pipeline',
      left: {
        label: 'No guardrails',
        items: [
          'Parse errors crash the app',
          'Toxic content reaches users',
          'Hallucinated data treated as fact',
          'No fallback path',
        ],
      },
      right: {
        label: 'Guardrail chain',
        items: [
          'Invalid schema → retry or fallback',
          'Blocked content → safe rejection',
          'Low confidence → "I\'m not sure"',
          'Every failure is loggable and testable',
        ],
      },
    },
  },
  // ---- Demo: Guardrails ----
  {
    type: 'title',
    content: {
      title: 'Demo — Guardrails',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 2',
      icon: 'rocket',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Field rules and exercises',
      icon: 'check-square',
    },
  },

  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 4',
      rules: [
        {
          rule: 'Count tokens before you send',
          example: 'Surprise truncation is worse than deliberate trimming.',
          icon: 'calculator',
        },
        {
          rule: 'Chain guardrails, never skip them',
          example: 'Schema → filter → confidence. Fail fast, log always.',
          icon: 'shield',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Build the Research Assistant',
      points: [
        '01 — Streaming chat API: FastAPI with SSE streaming endpoints',
        '02 — MCP research tools: web fetch + notes with a tool-calling loop',
        '03 — Multimodal: vision (GPT-4o image analysis) and audio (Whisper)',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 4 — Complete',
      subtitle: 'Next: RAG fundamentals',
      icon: 'check-circle',
    },
  },
];
