"""
Mock ship-system tools for Exercise 04 — Swarm Agents with Scoped Tools.

Each department gets domain tools plus transfer_to_* handoff tools.
"""
from __future__ import annotations

import json

DEPARTMENTS = ["comms", "engineering", "tactical"]

# --- Domain tool implementations (mock, deterministic) ---


def scan_frequencies() -> str:
    """List active subspace channels."""
    return (
        "Active channels: 142.7 MHz (distress beacon), 88.1 MHz (fleet command), "
        "201.3 MHz (encrypted — origin unknown)."
    )


def decrypt_signal(signal_id: str) -> str:
    """Decode an encrypted transmission."""
    return (
        f"Signal {signal_id} decoded: 'Request immediate power boost to relay array. "
        f"Reactor output must sustain +15% for 4 hours.'"
    )


def check_reactor() -> str:
    """Read current reactor status."""
    return (
        "Reactor: nominal at 94% capacity. Margins allow +18% sustained for 6 hours. "
        "Coolant stable, no anomalies."
    )


def run_diagnostic(system: str) -> str:
    """Run diagnostics on a named ship system."""
    return (
        f"Diagnostic [{system}]: all subsystems green. "
        f"Last maintenance cycle 12 days ago — within tolerance."
    )


def check_shields() -> str:
    """Report shield strength and configuration."""
    return "Shields: forward 87%, aft 91%, lateral 85%. Modulation set to standard."


def scan_threats() -> str:
    """Scan for hostile contacts in local space."""
    return (
        "No hostile contacts within 50,000 km. One unidentified vessel "
        "at long range — bearing 270, no weapons lock detected."
    )


def transfer_to_comms() -> str:
    return json.dumps({"transfer_to": "comms"})


def transfer_to_engineering() -> str:
    return json.dumps({"transfer_to": "engineering"})


def transfer_to_tactical() -> str:
    return json.dumps({"transfer_to": "tactical"})


TOOL_FUNCTIONS: dict[str, callable] = {
    "scan_frequencies": scan_frequencies,
    "decrypt_signal": decrypt_signal,
    "check_reactor": check_reactor,
    "run_diagnostic": run_diagnostic,
    "check_shields": check_shields,
    "scan_threats": scan_threats,
    "transfer_to_comms": transfer_to_comms,
    "transfer_to_engineering": transfer_to_engineering,
    "transfer_to_tactical": transfer_to_tactical,
}

_TRANSFER_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "transfer_to_comms",
            "description": (
                "Hand off to the Communications Officer for signals, "
                "decryption, and subspace relays."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_engineering",
            "description": (
                "Hand off to Engineering for reactor, diagnostics, and ship systems."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_tactical",
            "description": (
                "Hand off to Tactical for shields, threats, and defense."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

_DOMAIN_SCHEMAS: dict[str, list[dict]] = {
    "comms": [
        {
            "type": "function",
            "function": {
                "name": "scan_frequencies",
                "description": "Scan active subspace and radio frequencies.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "decrypt_signal",
                "description": "Decrypt an encrypted signal by ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "signal_id": {
                            "type": "string",
                            "description": "Signal identifier, e.g. X42",
                        }
                    },
                    "required": ["signal_id"],
                },
            },
        },
    ],
    "engineering": [
        {
            "type": "function",
            "function": {
                "name": "check_reactor",
                "description": "Check reactor output and capacity margins.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_diagnostic",
                "description": "Run diagnostics on a ship subsystem.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "system": {
                            "type": "string",
                            "description": "Subsystem name, e.g. life_support",
                        }
                    },
                    "required": ["system"],
                },
            },
        },
    ],
    "tactical": [
        {
            "type": "function",
            "function": {
                "name": "check_shields",
                "description": "Report current shield strength.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scan_threats",
                "description": "Scan for hostile contacts nearby.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ],
}


def _tools_for_department(department: str) -> list[dict]:
    """Domain tools plus transfer tools to other departments."""
    domain = _DOMAIN_SCHEMAS.get(department, [])
    transfers = [
        t
        for t in _TRANSFER_SCHEMAS
        if t["function"]["name"] != f"transfer_to_{department}"
    ]
    return domain + transfers


AGENT_TOOLS: dict[str, list[dict]] = {
    dept: _tools_for_department(dept) for dept in DEPARTMENTS
}

AGENT_PROMPTS: dict[str, str] = {
    "comms": (
        "You are the Communications Officer aboard the DSS Pathfinder. "
        "You handle signals, decryption, and subspace relays. "
        "Use your tools to gather data. If the question needs reactor, "
        "shields, or threat data, call transfer_to_engineering or "
        "transfer_to_tactical. When you have enough information, reply "
        "to the user in plain text without calling more tools."
    ),
    "engineering": (
        "You are the Chief Engineer aboard the DSS Pathfinder. "
        "You handle reactor output, diagnostics, and ship systems. "
        "Use your tools to gather data. If the question needs comms "
        "or tactical data, call the appropriate transfer tool. "
        "When you have enough information, reply in plain text."
    ),
    "tactical": (
        "You are the Tactical Officer aboard the DSS Pathfinder. "
        "You handle shields, threat scans, and defense. "
        "Use your tools to gather data. Hand off to comms or engineering "
        "when needed. When ready, answer the user in plain text."
    ),
}
