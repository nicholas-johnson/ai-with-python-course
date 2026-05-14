"""
Exercise 3: RAG MCP Server -- start.py (delegates build)
==========================================================
Console agent that connects to the RAG MCP server and chats using tool calling.

Run:  python start.py
"""

import asyncio
import json

# TODO: import OpenAI from openai
# TODO: import ClientSession, StdioServerParameters from mcp
# TODO: import stdio_client from mcp.client.stdio

SERVER_SCRIPT = "server.py"  # change to "solution_server.py" to test with the solution


# TODO: Implement mcp_to_openai_tools(mcp_tools) -> list[dict]
#   Convert MCP tool definitions to OpenAI function-calling format.
#   Each MCP tool has .name, .description, .inputSchema
#   Return a list of {"type": "function", "function": {...}} dicts.


# TODO: Implement the agent loop
# async def agent_loop(session, openai_tools, mcp_tools_map):
#     """Interactive agent loop with tool calling."""
#     client = OpenAI()
#     messages = [
#         {"role": "system", "content": "You are a research assistant with access to a document search system. Use the available tools to find and retrieve information."}
#     ]
#
#     while True:
#         user_input = input("\nYou: ").strip()
#         if not user_input:
#             continue
#         if user_input.lower() == "quit":
#             print("Goodbye!")
#             break
#         if user_input == "/tools":
#             for name, tool in mcp_tools_map.items():
#                 print(f"  - {name}: {tool.description}")
#             continue
#
#         messages.append({"role": "user", "content": user_input})
#
#         # Standard tool-calling loop:
#         # 1. Call OpenAI with messages + tools
#         # 2. If response has tool_calls, execute each via session.call_tool()
#         # 3. Append tool results to messages
#         # 4. Repeat until the LLM returns a text response


# TODO: Implement main()
# async def main():
#     server_params = StdioServerParameters(command="python", args=[SERVER_SCRIPT])
#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()
#             tools_result = await session.list_tools()
#             # convert tools, build map, run agent_loop


def main():
    print("TODO: implement the MCP client and agent loop.")
    print("See the README for step-by-step instructions.")


if __name__ == "__main__":
    main()
