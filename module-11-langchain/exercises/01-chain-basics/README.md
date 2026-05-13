# Exercise 01 — Chain Basics

**Mission briefing:** Build a LangChain **prompt template + chain** that classifies incoming crew reports into categories (navigation, engineering, science, medical) and returns a structured JSON summary.

## Objectives

1. Create a `ChatPromptTemplate` with system and human messages.
2. Pipe the template through a model and a `JsonOutputParser`.
3. Invoke the chain on sample crew reports and verify the output schema.

## Run the tests

```bash
pytest module-11-langchain/exercises/01-chain-basics/test_start.py -v
```
