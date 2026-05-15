export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 1 — Working with the LLM',
      subtitle: 'CLI, API, and streaming',
      icon: 'message-square',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'The user-facing layer',
      points: [
        'Module 0 covered Python fundamentals. This module adds the LLM interface layer.',
        'CLI, API, and session memory — the user-facing layer.',
        'Streaming makes the AI feel responsive, not stuck.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Build a **CLI chat loop** with conversation history.',
        'Create a **FastAPI streaming endpoint** (SSE).',
        'Implement **pluggable session storage**: in-memory, file-based.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'The chat loop',
      code: `class ChatBot:
    def __init__(self, llm, system_prompt):
        self.messages = [{"role": "system", "content": system_prompt}]

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        response = self.llm.chat(self.messages)
        self.messages.append({"role": "assistant", "content": response})
        return response`,
      highlights: [
        'History grows with every turn — the LLM sees full context',
        'Clear/truncate to manage token budgets',
      ],
    },
  },
  // ---- Demo: Basic chat ----
  {
    type: 'title',
    content: {
      title: 'Demo — Basic chat',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 1',
      icon: 'rocket',
    },
  },

  // ---- Section: Streaming ----
  {
    type: 'title',
    content: {
      title: 'Streaming',
      subtitle: 'Real-time tokens over Server-Sent Events',
      icon: 'zap',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Why streaming?',
      icon: 'zap',
      points: [
        'Users perceive streaming as **faster** even when total time is the same.',
        'First token appears in ~200ms vs waiting 2-5s for full response.',
        'Progressive rendering keeps the user engaged during generation.',
        'Server-Sent Events (SSE) — simple, HTTP-native, no WebSocket complexity.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'SSE streaming with FastAPI',
      code: `from sse_starlette.sse import EventSourceResponse

@app.post("/chat")
async def chat(request: ChatRequest):
    async def generate():
        yield {"event": "session", "data": json.dumps({"session_id": sid})}
        async for token in llm.stream(messages):
            yield {"event": "token", "data": json.dumps({"token": token})}
        yield {"event": "done", "data": json.dumps({"full_response": text})}

    return EventSourceResponse(generate())`,
      highlights: [
        'Each yield is an SSE event the client receives immediately',
        'Structured events: session, token, done',
      ],
    },
  },
  // ---- Demo: Streaming ----
  {
    type: 'title',
    content: {
      title: 'Demo — Streaming',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 2',
      icon: 'rocket',
    },
  },

  // ---- Section: Sessions ----
  {
    type: 'title',
    content: {
      title: 'Session management',
      subtitle: 'Pluggable persistence for conversation history',
      icon: 'layers',
    },
  },

  {
    type: 'comparison',
    content: {
      title: 'In-memory vs persistent sessions',
      left: {
        label: 'In-memory',
        items: [
          'Fast: plain dict lookup',
          'Lost on server restart',
          'Fine for development',
          'No shared state between instances',
        ],
      },
      right: {
        label: 'File / DB',
        items: [
          'Survives restarts',
          'Shareable across instances',
          'Slightly slower (disk/network I/O)',
          'Production-ready with Redis/Postgres',
        ],
      },
    },
  },
  {
    type: 'code',
    content: {
      title: 'Pluggable backend pattern',
      code: `class SessionBackend(Protocol):
    def load(self, session_id: str) -> list[dict]: ...
    def save(self, session_id: str, messages: list[dict]) -> None: ...
    def exists(self, session_id: str) -> bool: ...

class SessionManager:
    def __init__(self, backend: SessionBackend):
        self.backend = backend

# Swap backends without changing any other code
mgr = SessionManager(InMemoryBackend())
mgr = SessionManager(FileBackend(Path("./sessions")))`,
      highlights: [
        'Protocol: any object with load/save/exists works',
        'Same SessionManager code, different storage',
      ],
    },
  },
  // ---- Demo: Prompt engineering ----
  {
    type: 'title',
    content: {
      title: 'Demo — Prompt engineering',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 3',
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
      title: 'Field rules — Module 1',
      rules: [
        {
          rule: 'Stream by default',
          example: 'Waiting 5 seconds for a response feels broken.',
          icon: 'zap',
        },
        {
          rule: 'Sessions are backend-agnostic',
          example: 'Code to Protocol, not to dict or file.',
          icon: 'layers',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — Chat loop: conversation history and LLM interaction',
        '02 — Streaming API: FastAPI + SSE endpoint',
        '03 — Session manager: pluggable in-memory and file backends',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 1 — Complete',
      subtitle: 'Next: the agent core',
      icon: 'check-circle',
    },
  },
];
