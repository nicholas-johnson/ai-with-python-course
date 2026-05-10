export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 13 — Capstone Project',
      subtitle: 'Full stack agentic ops for the DSS Pathfinder',
      icon: 'rocket',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'All systems integrated',
      points: [
        'Everything you built — agent core, RAG, MCP tools, multi-agent — comes together.',
        'A full agentic application: chat, retrieval, tools, and coordinated agents.',
        'Demo scenarios, integration tests, and an extension checklist for the future.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Build a **full agentic app**: chat + RAG + MCP tools + multi-agent coordination.',
        'Write **demo scenarios** that show value to mission operations.',
        'Add **integration tests** that guard against regressions.',
        'Document **extension points** for tools, data sources, and policies.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Architecture overview',
      icon: 'layers',
      points: [
        '**Chat interface**: CLI or API — user sends questions, gets answers.',
        '**RAG pipeline**: ship logs, manuals, and star charts indexed and searchable.',
        '**MCP tool suite**: sensor reads, crew lookups, log queries.',
        '**Multi-agent path**: router → specialist → critic for complex questions.',
        '**Tracing**: every call logged with trace ID for debugging.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Capstone app skeleton',
      code: `class PathfinderAgent:
    def __init__(self, llm, tools, retriever, agents):
        self.llm = llm
        self.tools = tools
        self.retriever = retriever
        self.agents = agents
        self.memory = SessionMemory()

    def chat(self, user_input: str) -> str:
        self.memory.add({"role": "user", "content": user_input})

        if needs_retrieval(user_input):
            context = self.retriever.search(user_input)
        if needs_specialist(user_input):
            return self.agents.route(user_input)

        response = self.llm.chat(self.memory.get_messages())
        self.memory.add({"role": "assistant", "content": response})
        return response`,
      highlights: [
        'Decides per-query: direct answer, retrieval, or multi-agent',
        'Session memory persists across the conversation',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Demo scenarios',
      icon: 'play',
      points: [
        '**Simple Q&A**: "Who is the chief engineer?" → direct tool call.',
        '**RAG query**: "What happened during the Kepler Sweep?" → retrieval + grounded answer.',
        '**Multi-step**: "Compare hull integrity reports from last week" → decompose + retrieve + synthesise.',
        '**Multi-agent**: "Plan a rescue mission" → router → researcher → critic → final plan.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Integration testing',
      icon: 'check-square',
      points: [
        '**Happy path**: known question → expected tool calls → correct answer.',
        '**Failure path**: tool timeout → graceful fallback, not a crash.',
        '**Adversarial**: question with no answer → "I don\'t know", not a hallucination.',
        '**Mock the LLM** for deterministic tests; test with a live model separately.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Integration test structure',
      code: `def test_crew_query(agent, mock_llm):
    mock_llm.set_response(
        tool_calls=[{"name": "query_crew",
                      "arguments": {"department": "science"}}],
        final="3 crew in science: Voss, Chen, Morel.",
    )
    result = agent.chat("Who is in the science team?")

    assert "Voss" in result
    assert mock_llm.tool_calls_made == ["query_crew"]

def test_unknown_question(agent, mock_llm):
    mock_llm.set_response(
        final="I don't have enough information to answer."
    )
    result = agent.chat("What is the meaning of life?")
    assert "don't have" in result.lower()`,
      highlights: [
        'Mock LLM makes tests fast, free, and deterministic',
        'Test both success paths and graceful failure',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Extension checklist',
      icon: 'plus-square',
      points: [
        '**New tool**: add to the MCP server → update tool registry → write tests.',
        '**New data source**: chunk → embed → add to vector index → test retrieval.',
        '**New agent role**: define system prompt → register in router → test routing.',
        '**New policy**: add guardrail to the chain → test with adversarial inputs.',
        'Document each extension point so future engineers know where to plug in.',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'What you built over 3 days',
      left: {
        label: 'Day 1',
        items: [
          'Python fundamentals',
          'Agent core + tool loop',
          'LLM integration + streaming',
          'Prompt engineering + guardrails',
        ],
      },
      right: {
        label: 'Days 2-3',
        items: [
          'MCP server + tools',
          'RAG + knowledge graphs',
          'Multi-agent + memory',
          'Production + LangChain + capstone',
        ],
      },
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Capstone',
      rules: [
        {
          rule: 'Integration tests are not optional',
          example: 'The capstone must prove it works — demos and assertions.',
          icon: 'check-square',
        },
        {
          rule: 'Document extension points',
          example: 'If someone cannot add a tool without reading all the code, the architecture failed.',
          icon: 'file-text',
        },
        {
          rule: 'Ship it',
          example: 'A working demo beats a perfect plan. Launch, then iterate.',
          icon: 'rocket',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Final mission',
      points: [
        '01 — Capstone app: integrated chat + RAG + MCP + multi-agent',
        '02 — Test and extend: integration tests + extension documentation',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Mission complete — Module 13',
      subtitle: 'The Pathfinder AI is online. Well done, Engineer.',
      icon: 'party-popper',
    },
  },
];
