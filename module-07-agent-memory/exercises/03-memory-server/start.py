"""
Exercise 03: Memory MCP Server -- start.py
=============================================
Console agent that connects to the Memory MCP server and chats using tool calling.

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
#         {
#             "role": "system",
#             "content": (
#                 "You are a helpful assistant with access to a memory system. "
#                 "Use the remember tool to store important facts the user shares. "
#                 "Use the recall tool to retrieve relevant memories when answering. "
#                 "Use list_memories to see everything you know. "
#                 "Always check your memories before claiming you don't know something."
#             ),
#         }
#     ]
#
#     print("Type a message, /tools to list tools, or 'quit' to exit.\n")
#
#     while True:
#         user_input = input("You: ").strip()
#         if not user_input:
#             continue
#         if user_input.lower() == "quit":
#             print("Goodbye!")
#             break
#         if user_input == "/tools":
#             for name, tool in mcp_tools_map.items():
#                 desc = tool.description or "No description"
#                 print(f"  - {name}: {desc}")
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
# async def async_main():
#     server_params = StdioServerParameters(
#         command="python",
#         args=[SERVER_SCRIPT],
#     )
#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()
#             tools_result = await session.list_tools()
#             mcp_tools = tools_result.tools
#             openai_tools = mcp_to_openai_tools(mcp_tools)
#             mcp_tools_map = {t.name: t for t in mcp_tools}
#             print(f"Connected to Memory MCP server. {len(mcp_tools)} tools available.")
#             await agent_loop(session, openai_tools, mcp_tools_map)


def main():
    print("TODO: implement the MCP client and agent loop.")
    print("See the README for step-by-step instructions.")


if __name__ == "__main__":
    main()
