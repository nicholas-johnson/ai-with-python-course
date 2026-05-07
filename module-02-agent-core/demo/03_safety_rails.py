"""
Demo: Safety rails — allowlists, rate limits, redaction, audit logs.
Run:  python module-02-agent-core/demo/03_safety_rails.py
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pathfinder.safety")


@dataclass
class AuditEntry:
    timestamp: float
    tool_name: str
    arguments: dict
    result: str
    allowed: bool


class SafetyLayer:
    def __init__(
        self,
        allowed_tools: set[str],
        rate_limit: int = 10,
        rate_window: float = 60.0,
    ):
        self._allowed = allowed_tools
        self._rate_limit = rate_limit
        self._rate_window = rate_window
        self._call_times: list[float] = []
        self.audit_log: list[AuditEntry] = []
        self._redaction_patterns = [
            (re.compile(r"clearanceLevel[\"']?\s*[:=]\s*\d+"), "clearanceLevel: [REDACTED]"),
            (re.compile(r"api[_-]?key[\"']?\s*[:=]\s*[\"'][^\"']+[\"']", re.IGNORECASE), "api_key: [REDACTED]"),
        ]

    def check_allowed(self, tool_name: str) -> bool:
        if tool_name not in self._allowed:
            logger.warning("BLOCKED: tool '%s' not in allowlist", tool_name)
            return False
        return True

    def check_rate_limit(self) -> bool:
        now = time.time()
        self._call_times = [t for t in self._call_times if now - t < self._rate_window]
        if len(self._call_times) >= self._rate_limit:
            logger.warning("RATE LIMITED: %d calls in %.0fs window", len(self._call_times), self._rate_window)
            return False
        self._call_times.append(now)
        return True

    def redact(self, text: str) -> str:
        for pattern, replacement in self._redaction_patterns:
            text = pattern.sub(replacement, text)
        return text

    def audit(self, tool_name: str, arguments: dict, result: str, allowed: bool):
        entry = AuditEntry(
            timestamp=time.time(),
            tool_name=tool_name,
            arguments=arguments,
            result=self.redact(result),
            allowed=allowed,
        )
        self.audit_log.append(entry)
        status = "ALLOWED" if allowed else "BLOCKED"
        logger.info("AUDIT [%s] %s(%s)", status, tool_name, json.dumps(arguments))


if __name__ == "__main__":
    safety = SafetyLayer(
        allowed_tools={"get_crew_count", "ship_status"},
        rate_limit=3,
        rate_window=10.0,
    )

    print("=== Safety Rails Demo ===\n")

    print("1. Allowlist check:")
    print(f"   get_crew_count allowed? {safety.check_allowed('get_crew_count')}")
    print(f"   delete_all_data allowed? {safety.check_allowed('delete_all_data')}")

    print("\n2. Rate limiting (limit=3 per 10s):")
    for i in range(5):
        ok = safety.check_rate_limit()
        print(f"   Call {i + 1}: {'OK' if ok else 'BLOCKED'}")

    print("\n3. Redaction:")
    raw = '{"name": "Voss", "clearanceLevel": 5, "api_key": "sk-secret123"}'
    print(f"   Raw:     {raw}")
    print(f"   Redacted: {safety.redact(raw)}")

    print("\n4. Audit log:")
    safety.audit("get_crew_count", {"department": "science"}, '{"count": 3}', True)
    safety.audit("delete_all_data", {}, "", False)
    for entry in safety.audit_log:
        status = "ALLOWED" if entry.allowed else "BLOCKED"
        print(f"   [{status}] {entry.tool_name} -> {entry.result or '(blocked)'}")
