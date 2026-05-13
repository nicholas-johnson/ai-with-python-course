"""
Demo: CLI chat loop — conversation history, simulated streaming.
Run:  python module-01-working-with-the-llm/demo/01_chat_cli.py

Uses a mock LLM to simulate a streaming chat interface.
"""

import sys
import time


class MockStreamingLLM:
    """Simulates token-by-token streaming responses."""

    RESPONSES = {
        "hello": "Welcome aboard the DSS Pathfinder, Engineer. How can I assist you today?",
        "status": "All primary systems nominal. Warp core at 97% efficiency. Shields online. Long-range sensors show clear space ahead.",
        "crew": "Current bridge crew: Commander Voss (captain), Lt. Cmdr. Orin (science), Chief Engineer Chen, Lt. Petrov (navigation), Ensign Morel (ops).",
    }
    DEFAULT = "I'm the Pathfinder AI. I can help with ship status, crew queries, mission data, and system diagnostics. What do you need?"

    def stream(self, messages: list[dict]):
        last_user = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user = msg["content"].lower()
                break

        response = self.DEFAULT
        for keyword, text in self.RESPONSES.items():
            if keyword in last_user:
                response = text
                break

        for char in response:
            yield char
            time.sleep(0.015)


def run_chat():
    llm = MockStreamingLLM()
    history: list[dict] = [
        {"role": "system", "content": "You are the DSS Pathfinder ship AI. Be helpful, concise, and professional."},
    ]

    print("\n=== DSS Pathfinder AI Console ===")
    print("Type your message. Enter 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            print("\nPathfinder AI signing off.")
            break

        history.append({"role": "user", "content": user_input})

        sys.stdout.write("AI> ")
        sys.stdout.flush()

        full_response = []
        for token in llm.stream(history):
            sys.stdout.write(token)
            sys.stdout.flush()
            full_response.append(token)

        print()
        history.append({"role": "assistant", "content": "".join(full_response)})


if __name__ == "__main__":
    run_chat()
