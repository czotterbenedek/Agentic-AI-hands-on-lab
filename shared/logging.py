"""Structured logging utilities for observable agent execution."""

import sys
import logging
from typing import Any, Optional


class AgentLogger:
    """Formatted logger for agent reasoning steps, tool actions, and handoffs."""

    # ANSI colors for terminal output
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"

    def __init__(self, name: str = "Agent", verbose: bool = True):
        self.name = name
        self.verbose = verbose
        self.traces: list[dict[str, Any]] = []

    def log(self, step_type: str, content: Any, color: str = "") -> None:
        """Record and optionally print a trace step."""
        trace_item = {"agent": self.name, "type": step_type, "content": str(content)}
        self.traces.append(trace_item)
        if self.verbose:
            tag = f"{color}{self.BOLD}[{self.name} - {step_type}]{self.RESET}"
            print(f"{tag} {content}", file=sys.stderr)

    def thought(self, text: str) -> None:
        """Log internal reasoning thought."""
        self.log("THOUGHT", text, self.CYAN)

    def action(self, tool_name: str, args: Any) -> None:
        """Log tool invocation action."""
        self.log("ACTION", f"Calling tool `{tool_name}` with args: {args}", self.YELLOW)

    def observation(self, result: Any) -> None:
        """Log external tool execution result."""
        preview = str(result)
        if len(preview) > 300:
            preview = preview[:300] + "... [truncated]"
        self.log("OBSERVATION", preview, self.BLUE)

    def handoff(self, from_agent: str, to_agent: str, task: str) -> None:
        """Log multi-agent delegation event."""
        self.log("HANDOFF", f"{from_agent} -> {to_agent} | Task: {task}", self.MAGENTA)

    def final_answer(self, answer: str) -> None:
        """Log agent's final answer."""
        self.log("FINAL ANSWER", answer, self.GREEN)

    def error(self, err_msg: str) -> None:
        """Log execution error."""
        self.log("ERROR", err_msg, self.RED)

    def get_traces(self) -> list[dict[str, Any]]:
        """Return the collected trace history."""
        return list(self.traces)

    def clear(self) -> None:
        """Clear recorded traces."""
        self.traces.clear()
