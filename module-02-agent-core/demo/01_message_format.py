"""
Demo: Agent message format — the conversation state that drives a tool-using loop.
Run:  python module-02-agent-core/demo/01_message_format.py
"""

from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


def print_conversation(messages: list[Message]) -> None:
    for msg in messages:
        header = f"[{msg.role.upper()}]"
        if msg.name:
            header += f" ({msg.name})"
        if msg.tool_call_id:
            header += f" call_id={msg.tool_call_id}"

        print(f"\n{header}")
        if msg.content:
            print(f"  {msg.content}")
        for tc in msg.tool_calls:
            print(f"  -> tool_call: {tc.name}({tc.arguments})")


conversation: list[Message] = [
    Message(
        role="system",
        content=(
            "You are the DSS Pathfinder ship AI. You have access to tools for "
            "querying crew records, mission data, and ship systems. Always cite "
            "the data source in your answers."
        ),
    ),
    Message(
        role="user",
        content="Who is assigned to the Kepler Sweep mission?",
    ),
    Message(
        role="assistant",
        content=None,
        tool_calls=[
            ToolCall(
                id="call_001",
                name="query_crew",
                arguments={"active_mission": "MSN-001"},
            ),
        ],
    ),
    Message(
        role="tool",
        tool_call_id="call_001",
        name="query_crew",
        content='[{"id":"CRW-001","name":"Commander Elara Voss"},{"id":"CRW-003","name":"Chief Engineer Mira Chen"},{"id":"CRW-005","name":"Ensign Dax Morel"},{"id":"CRW-011","name":"Specialist Bodhi Kwan"}]',
    ),
    Message(
        role="assistant",
        content=(
            "The Kepler Sweep mission (MSN-001) has 4 crew assigned: "
            "Commander Elara Voss, Chief Engineer Mira Chen, Ensign Dax Morel, "
            "and Specialist Bodhi Kwan. (Source: crew manifest query)"
        ),
    ),
]

if __name__ == "__main__":
    print("=== Agent Conversation State ===")
    print_conversation(conversation)
    print("\n--- Key observations ---")
    print("1. System message sets the agent's behaviour and available tools.")
    print("2. Assistant can reply with content OR tool_calls (or both).")
    print("3. Tool results come back as role='tool' with the matching call_id.")
    print("4. The loop continues until the assistant replies with content only.")
