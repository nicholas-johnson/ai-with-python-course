# Exercise 3: RAG Chain

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

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

answer = rag_chain.invoke("What caused the reactor anomaly?")
```

`RunnablePassthrough()` passes the input string through unchanged (the question). The retriever fetches documents, `format_docs` formats them with source labels. The chain reads naturally: retrieve context, build prompt, call model, parse output.

## What you build

A console RAG agent in **`start.py`** that loads ship logs into ChromaDB, builds a retrieval chain, and answers questions with citations.

The Exercise 1 and 2 code (classifier chain, tools, agent) is already inlined at the top of `start.py` — you'll add the RAG chain below it.

**Key functions:**

| Function | Description |
|---|---|
| `load_documents()` | Load ship logs, return `(texts, metadatas)` |
| `build_vectorstore(texts, metadatas)` | Embed and store logs in ChromaDB |
| `build_rag_chain(vectorstore)` | Create the LCEL RAG chain, return `(chain, retriever)` |
| `ask(chain, retriever, question)` | Run a RAG query, return `(answer, retrieved_docs)` |

## Step-by-step

### 1. Load the ship logs

Load `data/ship_logs.json` from the project root. Each entry has `id`, `content`, `author`, and `category`.

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

Create a prompt that instructs the model to answer from the provided sources only, then pipe it all together:

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using ONLY the sources below. Cite sources as [Source N]. ..."),
    ("human", "Sources:\n{context}\n\nQuestion: {question}"),
])

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
```

### 5. Implement `ask`

Invoke the retriever separately to capture the source documents, then invoke the chain for the answer:

```python
def ask(chain, retriever, question: str) -> tuple[str, list]:
    docs = retriever.invoke(question)
    answer = chain.invoke(question)
    return answer, docs
```

### 6. Build the interactive loop

Handle these commands:

| Command | Action |
|---|---|
| any text | RAG chain — retrieve, ground, generate |
| `/sources` | Show the retrieved documents from the last query |
| `/norag` | Re-ask the last question without retrieval (compare quality) |
| `/agent` | Send the last question to the tool agent from Exercise 2 |
| `quit` | Exit |

## Try it

```bash
cd module-10-langchain/exercises/03-rag-chain
python start.py
```

Ask questions about the ship logs: mission status, engineering issues, crew activities, sensor anomalies. Use `/norag` to compare RAG answers with raw LLM answers.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `ask` returns a `(str, list)` tuple with a non-empty answer

## Stretch goals

- Add a reranker step between retrieval and generation
- Implement streaming output with `rag_chain.stream()`
- Add metadata filters (e.g., only search engineering logs)
