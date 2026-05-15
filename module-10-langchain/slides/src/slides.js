export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 10 — LangChain with Python',
      subtitle: 'Chains, agents, and RAG with LangChain',
      icon: 'link',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'From hand-rolled to framework',
      points: [
        'You built agents, tools, RAG, and multi-agent systems from scratch.',
        'LangChain wraps the same patterns into composable building blocks.',
        'This module bridges understanding with framework productivity.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Understand what **LangChain** provides vs. building from scratch.',
        'Use **prompt templates**, **output parsers**, and **chains**.',
        'Rewrite the hand-rolled agent loop with **LangChain agents + tools**.',
        'Connect LangChain to **MCP tools** and **RAG pipelines** from earlier modules.',
      ],
    },
  },
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
        '**Agent + Tools**: LLM decides which tools to call and when.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Prompt template + chain',
      code: `from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify support tickets as: routine, urgent, critical. "
               "Return JSON: {{category, summary}}"),
    ("user", "{report}"),
])

chain = prompt | ChatOpenAI(model="gpt-4o-mini") | JsonOutputParser()

result = chain.invoke({"report": "Server CPU usage exceeded 95%"})
# {"category": "critical", "summary": "Server CPU spike"}`,
      highlights: [
        'The pipe operator (|) chains steps: prompt → model → parser',
        'Each step is independently testable and swappable',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Hand-rolled vs LangChain',
      left: {
        label: 'Hand-rolled',
        items: [
          'Full control over every detail',
          'No framework dependency',
          'You write the retry / parse / routing logic',
          'Better for learning fundamentals',
        ],
      },
      right: {
        label: 'LangChain',
        items: [
          'Composable building blocks',
          'Batteries included (tools, memory, RAG)',
          'Faster to prototype',
          'Abstraction hides details (harder to debug)',
        ],
      },
    },
  },
  {
    type: 'standard',
    content: {
      title: 'LangChain tools',
      icon: 'wrench',
      points: [
        'Wrap any Python function as a LangChain **@tool**.',
        'The decorator generates the schema from type hints + docstring.',
        'Same concept as MCP tools — different interface.',
        'AgentExecutor handles the tool-calling loop for you.',
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
def read_metrics(metric_id: str) -> str:
    """Read the current value of a system metric."""
    return json.dumps(metrics[metric_id])

@tool
def lookup_users(role: str) -> str:
    """Look up users by role."""
    return json.dumps([u for u in users if u["role"] == role])

tools = [read_metrics, lookup_users]
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

result = executor.invoke({"input": "Who is in the backend team?"})`,
      highlights: [
        '@tool decorator = schema from type hints + docstring',
        'AgentExecutor runs the loop: LLM → tool call → result → repeat',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'LangChain RAG',
      icon: 'book-open',
      points: [
        '**Retriever**: any object with a `.invoke(query)` that returns documents.',
        '**RetrievalQA / LCEL chain**: retriever → format docs → LLM → answer.',
        'Works with ChromaDB, FAISS, Pinecone, or your custom vector store.',
        'Compare: your Module 5 RAG pipeline reimplemented in ~10 lines.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'RAG chain with LCEL',
      code: `from langchain_core.runnables import RunnablePassthrough

def format_docs(docs):
    return "\\n\\n".join(d.page_content for d in docs)

rag_chain = (
    {"context": retriever | format_docs,
     "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

answer = rag_chain.invoke("What caused the Q4 outage?")`,
      highlights: [
        'Retriever runs in parallel with question passthrough',
        'Same RAG pattern as Module 5 — LangChain just wires it up',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'When to use a framework',
      icon: 'scale',
      points: [
        '**Use LangChain** when you want fast prototyping and standard patterns.',
        '**Skip it** when you need full control or minimal dependencies.',
        'Understand the pattern first (you already do), then decide on tooling.',
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
          rule: 'Understand the pattern, then pick the tool',
          example: 'LangChain is faster only if you know what it is doing underneath.',
          icon: 'layers',
        },
        {
          rule: 'Test chains as units',
          example: 'Each chain step should be independently verifiable.',
          icon: 'check-square',
        },
        {
          rule: 'Pin framework versions',
          example: 'LangChain moves fast — unversioned deps break silently.',
          icon: 'lock',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Framework-powered ops',
      points: [
        '01 — Chain basics: prompt templates, output parsers, ticket classification',
        '02 — Tool agent: wrap custom tools as LangChain tools, run via AgentExecutor',
        '03 — RAG chain: RetrievalQA over a document knowledge base',
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
