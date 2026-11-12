"""Data structures, schemas, and shared blackboard context for multi-agent systems."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentRole(str, Enum):
    """Specialized agent roles in the academic multi-agent ecosystem."""
    SUPERVISOR = "supervisor"
    RESEARCHER = "researcher"
    ANALYST = "analyst"


@dataclass
class HandoffMessage:
    """Structured message passed when delegating a task between agents."""
    source_agent: str
    target_agent: str
    task_description: str
    context_payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_agent,
            "target": self.target_agent,
            "task": self.task_description,
            "payload_keys": list(self.context_payload.keys()),
            "timestamp": self.timestamp,
        }


@dataclass
class SharedContext:
    """Shared blackboard workspace accessible by supervisor and specialists."""
    raw_query: str
    retrieved_papers: List[Dict[str, Any]] = field(default_factory=list)
    analysis_artifacts: Dict[str, Any] = field(default_factory=dict)
    final_synthesis: Optional[str] = None
    delegation_history: List[HandoffMessage] = field(default_factory=list)

    def record_handoff(self, handoff: HandoffMessage) -> None:
        """Record delegation step in execution history."""
        self.delegation_history.append(handoff)

    def get_trace_summary(self) -> List[str]:
        """Return human-readable sequence of agent delegation hops."""
        return [
            f"[{h.source_agent}] -> [{h.target_agent}]: {h.task_description}"
            for h in self.delegation_history
        ]
