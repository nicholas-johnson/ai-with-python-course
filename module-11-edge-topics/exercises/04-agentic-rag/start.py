"""
Exercise 04 — Agentic RAG

The agent decides whether to retrieve, what to search for,
and when it has enough information to answer.
"""

from openai import OpenAI


SEARCH_TOOL = {
    # TODO: Define an OpenAI function-calling tool for document search.
    # It should have:
    # - type: "function"
    # - function.name: "search_documents"
    # - function.description: describe what the tool does
    # - function.parameters: a "query" string parameter (required)
}


def handle_tool_call(tool_call, search_fn) -> str:
    """
    Execute a tool call and return the result as a JSON string.

    Args:
        tool_call: An OpenAI tool call object with .function.name and .function.arguments.
        search_fn: A function that takes a query string and returns a list of results.

    Returns:
        JSON string of the search results.

    TODO:
    - Parse the tool call arguments (JSON string → dict)
    - If the function name is "search_documents", call search_fn with the query
    - Return the results as a JSON string
    """
    # TODO: implement tool call handling
    pass


def agentic_rag(
    client: OpenAI,
    question: str,
    search_fn,
    max_turns: int = 5,
) -> str:
    """
    Run an agentic RAG loop.

    The agent receives the question and can call search_documents
    as many times as needed before producing a final answer.

    Args:
        client: OpenAI client.
        question: The user's question.
        search_fn: Function that takes a query and returns search results.
        max_turns: Maximum number of tool-use turns.

    Returns:
        The agent's final text answer.

    TODO:
    - Initialize messages with a system prompt and the user question
    - Loop: call the LLM with tools available
    - If the response has tool_calls, handle each one and append results
    - If the response has no tool_calls, return the text content
    - Respect max_turns to prevent infinite loops
    """
    # TODO: implement the agentic RAG loop
    pass
