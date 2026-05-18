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
        'Multimodal: **vision**/image analysis, **speech-to-text** (Whisper).',
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

  // ---- Section A: Model selection + tokens ----
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

  // ---- Section B: AI in the browser ----
  {
    type: 'title',
    content: {
      title: 'AI in the browser',
      subtitle: 'SSE streaming and MCP tool integration',
      icon: 'globe',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Server-Sent Events (SSE)',
      icon: 'wifi',
      points: [
        '**One-way channel** from server to client over plain HTTP — no WebSocket handshake needed.',
        'Perfect for LLM streaming: each token arrives as it is generated.',
        'FastAPI + `sse-starlette`: wrap an **async generator** in `EventSourceResponse`.',
        'Four event types: `token` (incremental text), `tool_call`, `tool_result`, `done` (final message).',
        'The browser reads events with `EventSource` or a `fetch` + `ReadableStream`.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'SSE streaming pattern',
      code: `@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        stream = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, stream=True
        )
        full = ""
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                full += token
                yield {"event": "token",
                       "data": json.dumps({"token": token})}

        yield {"event": "done",
               "data": json.dumps({"role": "assistant", "content": full})}

    return EventSourceResponse(generate())`,
      highlights: [
        'The async generator yields dicts with "event" and "data" keys',
        'EventSourceResponse handles the SSE wire format automatically',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'MCP tools in a web API',
      icon: 'server',
      points: [
        '**Lifespan**: on startup, spawn the MCP server as a subprocess and connect via stdio.',
        '**Discovery**: call `session.list_tools()` and convert schemas to OpenAI function-calling format.',
        '**Tool-calling loop**: LLM returns `tool_calls` → execute via MCP → feed results back → repeat.',
        'Stream **tool_call** and **tool_result** SSE events so the frontend can show progress.',
        'On shutdown, clean up the MCP session and subprocess.',
      ],
    },
  },

  // ---- Section C: Multimodal ----
  {
    type: 'title',
    content: {
      title: 'Multimodal — see and hear',
      subtitle: 'Vision with GPT-4o and audio with Whisper',
      icon: 'image',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Multimodal inputs',
      icon: 'image',
      points: [
        '**Vision**: send images as base64 data URIs or public URLs in user messages.',
        '**Audio input**: Whisper API transcribes speech to text.',
        'Same chat completions API — content is just a **list of parts** instead of a string.',
        'Use `response_format: {"type": "json_object"}` to get structured vision output.',
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
    type: 'code',
    content: {
      title: 'Audio — Whisper transcription',
      code: `import io

audio_file = io.BytesIO(audio_bytes)
audio_file.name = "recording.wav"

transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
)
print(transcript.text)  # "Hello, this is a voice memo about..."`,
      highlights: [
        'Whisper accepts file-like objects — wrap raw bytes in BytesIO',
        'Set .name so the API knows the audio format',
      ],
    },
  },

  // ---- Section D: Guardrails ----
  {
    type: 'title',
    content: {
      title: 'Guardrails — defence in depth',
      subtitle: 'Schema validation, content filters, confidence gates',
      icon: 'shield',
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

  // ---- Demo ----
  {
    type: 'title',
    content: {
      title: 'Demo — Multimodal',
      subtitle: 'Switch to terminal: python demo/demo.py',
      icon: 'rocket',
    },
  },

  // ---- Wrap-up ----
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
        '01 — Research chat: streaming chat with MCP tool calling (server provided)',
        '02 — Multimodal: add vision (GPT-4o image analysis) and audio (Whisper)',
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
