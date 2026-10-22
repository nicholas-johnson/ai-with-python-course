# Exercise 3: RAG Chain

> **Scenario:** Hands-on work uses the **CSS Horizon** and `module-10-langchain/exercises/data/horizon_logs.json`. Module demos use the **DSS Pathfinder** and `data/ship_logs.json` at the repo root.

## Recap

In Module 5 you built a RAG pipeline by hand — chunk, embed, store, retrieve, ground, generate. LangChain wraps this in a retrieval chain where each step is a composable LCEL component.

**Retriever** — any object with an `.invoke(query)` method that returns documents. LangChain has built-in wrappers for ChromaDB, FAISS, Pinecone, etc:

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

vectorstore = Chroma.from_texts(texts, OpenAIEmbeddings(), metadatas=metadatas)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

**LCEL retrieval chain** — the retriever runs in parallel with a question passthrough, then feeds into the prompt:

```python
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

answer_chain = (
    RunnablePassthrough.assign(context=lambda x: format_docs(x["docs"]))
    | prompt
    | model
    | StrOutputParser()
)
rag_chain = (
    {"docs": retriever, "question": RunnablePassthrough()}
    | RunnablePassthrough.assign(answer=answer_chain)
)

result = rag_chain.invoke("What caused the reactor anomaly?")
# {"question": "...", "docs": [Document, ...], "answer": "..."}
```

`RunnablePassthrough()` passes the input string through unchanged (the question). `RunnablePassthrough.assign(...)` keeps everything already in the dict and adds a new key — so the result carries both the answer *and* the documents it was grounded on, from one retrieval. The chain reads naturally: retrieve context, build prompt, call model, parse output.

## What you build

A console RAG agent in **`start.py`** that loads ship logs into ChromaDB, builds a retrieval chain, and answers questions with citations.

The Exercise 1 and 2 code (classifier chain, tools, agent) is already inlined at the top of `start.py` — you'll add the RAG chain below it.

**Key functions:**

| Function | Description |
|---|---|
| `load_documents()` | Load ship logs, return `(texts, metadatas)` |
| `build_vectorstore(texts, metadatas)` | Embed and store logs in ChromaDB |
| `build_rag_chain(vectorstore)` | Create the LCEL RAG chain, return `(chain, retriever)` |
| `ask(chain, question)` | Run a RAG query, return `(answer, retrieved_docs)` |
| `build_rag_agent(retriever)` | The Exercise 2 agent plus a `search_logs` tool — agentic RAG |
| `run_rag_agent(agent, question)` | Run the RAG agent, return its final answer |

## Step-by-step

### 1. Load the ship logs

Load `module-10-langchain/exercises/data/horizon_logs.json`. Each entry has `id`, `content`, `author`, and `category`.

```python
EXERCISE_DATA = Path(__file__).resolve().parents[1] / "data"
logs = json.loads((EXERCISE_DATA / "horizon_logs.json").read_text())
```

### 2. Build the vectorstore

Use LangChain's ChromaDB wrapper to embed and store the logs:

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

texts = [log["content"] for log in logs]
metadatas = [{"source": log["id"], "author": log["author"], "category": log["category"]} for log in logs]

vectorstore = Chroma.from_texts(texts, OpenAIEmbeddings(), metadatas=metadatas)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

### 3. Create `format_docs`

Format retrieved documents with source labels for citations:

```python
def format_docs(docs):
    return "\n\n".join(
        f"[Source {i+1}: {doc.metadata.get('source', '?')}] {doc.page_content}"
        for i, doc in enumerate(docs)
    )
```

### 4. Build the RAG chain

Create a prompt that instructs the model to answer from the provided sources only, then compose the chain from the recap above so it returns the docs and the answer together:

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using ONLY the sources below. Cite sources as [Source N]. ..."),
    ("human", "Sources:\n{context}\n\nQuestion: {question}"),
])
```

### 5. Implement `ask`

One call to the chain gives you everything:

```python
def ask(chain, question: str) -> tuple[str, list]:
    result = chain.invoke(question)
    return result["answer"], result["docs"]
```

(A common mistake is calling `retriever.invoke()` and then `chain.invoke()` — that retrieves twice and the docs you show might not be the ones the answer used.)

### 6. Agentic RAG

A chain *always* retrieves, once, with the user's exact words. An agent can decide whether to search, rewrite the query, or search several times. Wrap the retriever as a tool and add it to the Exercise 2 agent:

```python
def build_rag_agent(retriever):
    @tool
    def search_logs(query: str) -> str:
        """Search the CSS Horizon ship logs. Use for questions about past events, surveys, or operations."""
        return format_docs(retriever.invoke(query))

    return create_agent(model, [*tools, search_logs], system_prompt=SYSTEM_PROMPT)
```

Compare the two with `/agent`: ask something that needs logs *and* a live sensor reading ("Is the docking seal better now than after the L5-Prime patch?") — only the agent can combine them.

### 7. Build the interactive loop

Handle these commands:

| Command | Action |
|---|---|
| any text | RAG chain — retrieve, ground, generate |
| `/sources` | Show the retrieved documents from the last query |
| `/norag` | Re-ask the last question without retrieval (compare quality) |
| `/agent` | Send the last question to the RAG agent (tools + `search_logs`) |
| `quit` | Exit |

## Try it

```bash
cd module-10-langchain/exercises/03-rag-chain
python start.py
```

Ask questions about Horizon logs: Lagrange resupply, Theta-9 survey, docking seals, cargo operations. Use `/norag` to compare RAG answers with raw LLM answers.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `load_documents` returns matching texts and metadata with `source`, `author`, `category`
- `ask` returns a non-empty answer and the retrieved documents (integration — needs `OPENAI_API_KEY`)
- the RAG agent has a `search_logs` tool (integration)

## Stretch goals

- Add a reranker step between retrieval and generation
- Stream just the answer: `answer_chain.stream({"docs": docs, "question": q})`
- Add metadata filters (e.g., only search engineering logs)
