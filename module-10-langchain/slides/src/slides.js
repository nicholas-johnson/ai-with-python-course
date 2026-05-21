export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 10 — LangChain with Python',
      subtitle: 'Automate the patterns you already know',
      icon: 'link',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Build **LCEL chains**: prompt templates, output parsers, and the pipe operator.',
        'Wrap functions as **LangChain tools** and run them via **AgentExecutor**.',
        'Construct a **RAG chain** with a LangChain retriever and ChromaDB.',
        'Know when to use LangChain and when to stay hand-rolled.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'What is LangChain?',
      icon: 'link',
      points: [
        'A Python/JS **framework for building LLM-powered applications** — the most widely adopted in the ecosystem.',
        'Standardises interfaces between components so they compose together (prompt, model, parser, retriever, tools).',
        'Huge integration surface: 100+ model providers, 50+ vector stores, document loaders, memory systems.',
        'Every chain is automatically **streamable**, **batchable**, and **invocable** — no extra wiring.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'What can you build with it?',
      icon: 'layers',
      points: [
        '**Chains** — prompt to model to structured output in one line.',
        '**Tool agents** — LLM decides which functions to call, framework runs the loop.',
        '**RAG pipelines** — retrieval, context injection, and generation wired together.',
        '**Beyond this module**: memory, conversation management, document ingestion, multi-model routing, evaluation.',
      ],
    },
  },

  {
    type: 'standard',
    content: {
      title: 'The broader ecosystem',
      icon: 'globe',
      points: [
        '**LangGraph** — stateful, graph-based multi-agent workflows (cycles, branching, human-in-the-loop).',
        '**LangSmith** — tracing and observability for debugging chains in production.',
        '**LangServe** — deploy any chain as a REST API with one command.',
        'We focus on core LangChain in this module — the rest builds on top.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'How does the pipe (|) work?',
      icon: 'plug',
      points: [
        'The `|` **looks** like a Unix pipe — it is **real Python**. LangChain defines what `|` means for its own objects.',
        'Every chain step (prompt, model, parser) is a **Runnable**: anything with `.invoke()`, `.stream()`, and `.batch()`.',
        '`prompt | model | parser` uses **operator overloading** — Python calls `__or__` and builds a **RunnableSequence** (a recipe, not a result).',
        'Nothing runs until you call **`.invoke()`** — then output flows left to right, same as three manual `.invoke()` calls in Demo 1.',
        'You can only pipe **LangChain Runnables** — plain strings or unrelated types will not work.',
      ],
    },
  },

  // ---- Section: LCEL chains ----
  {
    type: 'standard',
    content: {
      title: 'LangChain building blocks',
      icon: 'box',
      points: [
        '**PromptTemplate**: reusable prompts with variables.',
        '**ChatModel**: LLM wrapper (OpenAI, Anthropic, local models).',
        '**OutputParser**: structured extraction from model responses.',
        '**Chain (LCEL)**: compose steps with the `|` pipe operator.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'LCEL chain — prompt | model | parser',
      code: `from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify crew reports as: navigation, engineering, "
               "science, medical, operations. "
               "Return JSON: {{category, summary, priority}}"),
    ("human", "{report}"),
])

model = ChatOpenAI(model="gpt-4o-mini")

json_parser = JsonOutputParser()

chain = prompt | model | json_parser

result = chain.invoke({"report": "Plasma conduit 7-B ruptured"})
# {"category": "engineering", "summary": "...", "priority": "high"}`,
      highlights: [
        'The pipe operator (|) chains steps: prompt → model → parser',
        'Each step is independently testable and swappable',
      ],
    },
  },
  // ---- Demo: Chains and prompts ----
  {
    type: 'title',
    content: {
      title: 'Demo — Chains and prompts',
      subtitle: 'Switch to terminal: python demo/01_chains_and_prompts.py',
      icon: 'rocket',
    },
  },

  // ---- Section: Tool agents ----
  {
    type: 'title',
    content: {
      title: 'LangChain tools and agents',
      subtitle: 'The tool-calling loop, automated',
      icon: 'wrench',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'From @tool to AgentExecutor',
      icon: 'wrench',
      points: [
        'The **@tool** decorator generates JSON Schema from type hints + docstring.',
        '`create_tool_calling_agent` builds the agent from model + tools + prompt.',
        '**AgentExecutor** runs the loop: LLM → tool call → result → repeat.',
        '`verbose=True` prints the full thought/action/observation trace.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Tool-calling agent',
      code: `from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor

@tool
def read_sensor(sensor_name: str) -> str:
    """Read the current value of a ship sensor."""
    data = SENSOR_DATA.get(sensor_name)
    if not data:
        return json.dumps({"error": f"Unknown sensor '{sensor_name}'"})
    return json.dumps(data)

@tool
def query_crew(department: str) -> str:
    """Look up crew members by department."""
    return json.dumps([c for c in CREW if c["department"] == department])

tools = [read_sensor, query_crew]
agent = create_tool_calling_agent(model, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "What is the shield integrity?"})`,
      highlights: [
        '@tool decorator = schema from type hints + docstring',
        'AgentExecutor handles the loop — same pattern as Module 2',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Hand-rolled vs LangChain',
      left: {
        label: 'Hand-rolled (Module 2)',
        items: [
          'Full control over the loop',
          'No framework dependency',
          'You write retry / parse / routing',
          'Easier to debug',
        ],
      },
      right: {
        label: 'LangChain',
        items: [
          'Composable building blocks',
          'Batteries included (tools, memory, RAG)',
          'Faster to prototype standard patterns',
          'Abstraction hides details',
        ],
      },
    },
  },
  // ---- Demo: LangChain agents ----
  {
    type: 'title',
    content: {
      title: 'Demo — LangChain agents',
      subtitle: 'Switch to terminal: python demo/02_langchain_agents.py',
      icon: 'rocket',
    },
  },

  // ---- Section: RAG chains ----
  {
    type: 'title',
    content: {
      title: 'RAG with LangChain',
      subtitle: 'Retrieval chains in a few lines',
      icon: 'book-open',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'LangChain RAG components',
      icon: 'book-open',
      points: [
        '**Retriever**: `.invoke(query)` returns documents. Wraps ChromaDB, FAISS, etc.',
        '**format_docs**: formats retrieved passages with source labels.',
        '**RunnablePassthrough**: passes the question through unchanged.',
        'The chain: retriever | format → prompt → model → parser.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'RAG chain with LCEL',
      code: `from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough

vectorstore = Chroma.from_texts(texts, OpenAIEmbeddings(), metadatas=metas)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

def format_docs(docs):
    return "\\n\\n".join(
        f"[Source {i+1}: {d.metadata['source']}] {d.page_content}"
        for i, d in enumerate(docs)
    )

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | model | StrOutputParser()
)`,
      highlights: [
        'Chroma.from_texts() — embed and store in one call',
        'Same RAG pattern as Module 5, wired up with LCEL',
      ],
    },
  },
  // ---- Demo: LangChain RAG ----
  {
    type: 'title',
    content: {
      title: 'Demo — LangChain RAG',
      subtitle: 'Switch to terminal: python demo/03_langchain_rag.py',
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
    type: 'standard',
    content: {
      title: 'When to use a framework',
      icon: 'scale',
      points: [
        '**Use LangChain** for standard patterns: chains, tool agents, RAG.',
        '**Skip it** when you need full control or minimal dependencies.',
        'You already know the patterns — the framework just accelerates them.',
        'Frameworks change fast — fundamentals endure.',
      ],
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 10',
      rules: [
        {
          rule: 'Know the pattern, then pick the tool',
          example: 'LangChain is faster only if you know what it does underneath.',
          icon: 'layers',
        },
        {
          rule: 'Keep verbose=True during development',
          example: 'The trace shows every tool call and decision.',
          icon: 'check-square',
        },
        {
          rule: 'Know when to eject',
          example: 'If the framework fights you, go back to plain Python.',
          icon: 'lock',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — Chain basics: LCEL chain that classifies crew reports',
        '02 — Tool agent: wraps the classifier + ship tools in AgentExecutor (builds on 01)',
        '03 — RAG chain: adds retrieval to the agent over ship logs (builds on 02)',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 10 — Complete',
      subtitle: 'Next: edge topics',
      icon: 'check-circle',
    },
  },
];
