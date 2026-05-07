# Module 12 — LangChain with Python

**Framework-powered AI.** You have built agents, tools, RAG pipelines, and multi-agent systems from scratch. Now see how LangChain wraps the same patterns — chains, prompt templates, tool integrations, memory, and retrieval — into composable building blocks. This module bridges hand-rolled understanding with framework productivity.

## Learning goals

- Understand what **LangChain** provides vs. building from scratch: chains, agents, tools, memory, and output parsers.
- Rewrite a **hand-rolled agent loop** using LangChain components and compare the trade-offs.
- Connect LangChain to an **MCP server** and **RAG pipeline** built in earlier modules.

## Instructor notes

- **Chains and prompts** (`demo/01_chains_and_prompts.py`): prompt templates, output parsers, and chaining steps together.
- **LangChain agents** (`demo/02_langchain_agents.py`): agent executor with custom tools — compare to the module-02 hand-rolled loop.
- **LangChain RAG** (`demo/03_langchain_rag.py`): retrieval chain connecting to the vector store from module 06.

## Demos

```bash
python module-12-langchain/demo/01_chains_and_prompts.py
python module-12-langchain/demo/02_langchain_agents.py
python module-12-langchain/demo/03_langchain_rag.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-chain-basics`](exercises/01-chain-basics/) | Build a prompt-template + chain that classifies crew reports. |
| [`exercises/02-tool-agent`](exercises/02-tool-agent/) | Wrap ship tools from module 05 as LangChain tools, run via AgentExecutor. |
| [`exercises/03-rag-chain`](exercises/03-rag-chain/) | Assemble a LangChain RetrievalQA chain over the Pathfinder knowledge base. |

Run tests for this module:

```bash
pytest module-12-langchain/
```

## Slides

From repo root: `pnpm slides:12`, or `cd module-12-langchain/slides && pnpm dev`.

## Reference

- [LangChain Python docs](https://python.langchain.com/docs/)
- [LangChain Expression Language (LCEL)](https://python.langchain.com/docs/concepts/lcel/)
- [LangChain tool calling](https://python.langchain.com/docs/how_to/tool_calling/)
- [LangChain RAG tutorial](https://python.langchain.com/docs/tutorials/rag/)
