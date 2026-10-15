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
        'Wrap functions as **LangChain tools** and run them with **create_agent**.',
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
        '**LangChain 1.x agents** run on LangGraph — `create_agent` plus middleware.',
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

model = ChatOpenAI(model=MODEL, reasoning_effort="none")

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
      title: 'From @tool to create_agent',
      icon: 'wrench',
      points: [
        'The **@tool** decorator generates JSON Schema from type hints + docstring.',
        '`create_agent` builds the agent from model + tools + system prompt.',
        'It runs the loop: LLM → tool call → result → repeat (on LangGraph).',
        '`result["messages"]` holds every tool call and result — print it for a trace.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Tool-calling agent',
      code: `from langchain_core.tools import tool
from langchain.agents import create_agent

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
agent = create_agent(model, tools, system_prompt="You are the Pathfinder AI.")

result = agent.invoke({"messages": [{"role": "user", "content": "What is the shield integrity?"}]})
print(result["messages"][-1].text)`,
      highlights: [
        '@tool decorator = schema from type hints + docstring',
        'create_agent handles the loop — same pattern as Module 2',
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

  // ---- Section: Serving chains ----
  {
    type: 'title',
    content: {
      title: 'Serving chains as APIs',
      subtitle: 'python module-10-langchain/demo/04_serving_chains.py',
      icon: 'plug',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'A chain is already an API',
      icon: 'plug',
      points: [
        'Every **Runnable** has `ainvoke`, `abatch`, and `astream` — wrap them in **FastAPI** routes.',
        'Pydantic validates every request; OpenAPI docs are generated automatically.',
        'Older tutorials use **LangServe** `add_routes` — it is unmaintained and conflicts with current deps.',
        'For deploying **agents**, LangChain points to **LangGraph / LangSmith deployment**.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Chain to API in a few lines',
      code: `from fastapi import FastAPI
from pydantic import BaseModel

chain = prompt | ChatOpenAI(model=MODEL, reasoning_effort="none") | JsonOutputParser()

class ReportInput(BaseModel):
    report: str

class InvokeRequest(BaseModel):
    input: ReportInput

app = FastAPI(title="Report API")

@app.post("/classify/invoke")
async def classify_invoke(req: InvokeRequest):
    return {"output": await chain.ainvoke(req.input.model_dump())}`,
      highlights: [
        'Same LCEL chain as demo 01 — ainvoke inside an async route',
        'Run with: uvicorn server:app --reload',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Endpoints in the demo',
      icon: 'globe',
      points: [
        '**POST /classify/invoke** — body `{"input": {"report": "..."}}` → `{"output": {category, summary, priority}}`.',
        '**POST /classify/batch** — `chain.abatch(...)` over several reports.',
        '**POST /classify/stream** — `chain.astream(...)` + `StreamingResponse` (NDJSON of the partial result).',
        'Your FastAPI app can add ordinary routes too (e.g. `GET /health`).',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — Serving chains',
      subtitle: 'Switch to terminal: python module-10-langchain/demo/04_serving_chains.py',
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
          rule: 'Inspect the message trace during development',
          example: 'result["messages"] (or LangSmith) shows every tool call and decision.',
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
        '02 — Tool agent: wraps the classifier + ship tools with create_agent (builds on 01)',
        '03 — RAG chain: adds retrieval to the agent over ship logs (builds on 02)',
        '04 — Chain API: expose the Horizon classifier as a FastAPI service',
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
