"""Data structures, schemas, and shared blackboard context for multi-agent systems."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class AgentRole(str, Enum):
    """Specialized agent roles in the academic multi-agent ecosystem."""
    SUPERVISOR = "supervisor"
    RESEARCHER = "researcher"
    ANALYST = "analyst"


class AgentState(TypedDict, total=False):
    """LangGraph shared state dictionary passed across nodes and edges."""
    query: str
    messages: List[Dict[str, Any]]
    retrieved_papers: List[Dict[str, Any]]
    analysis_artifacts: Dict[str, Any]
    next_step: str  # "researcher", "analyst", "finish", or "__end__"
    iteration_count: int
    delegation_history: List[Dict[str, Any]]
    final_report: Optional[str]


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

    def to_agent_state(self) -> AgentState:
        """Convert SharedContext to LangGraph AgentState format."""
        return {
            "query": self.raw_query,
            "messages": [],
            "retrieved_papers": self.retrieved_papers,
            "analysis_artifacts": self.analysis_artifacts,
            "next_step": "supervisor",
            "iteration_count": len(self.delegation_history),
            "delegation_history": [h.to_dict() for h in self.delegation_history],
            "final_report": self.final_synthesis,
        }

    @classmethod
    def from_agent_state(cls, state: AgentState) -> "SharedContext":
        """Instantiate SharedContext from a completed LangGraph AgentState."""
        ctx = cls(
            raw_query=state.get("query", ""),
            retrieved_papers=state.get("retrieved_papers", []),
            analysis_artifacts=state.get("analysis_artifacts", {}),
            final_synthesis=state.get("final_report"),
        )
        for h_dict in state.get("delegation_history", []):
            if isinstance(h_dict, dict):
                ctx.record_handoff(
                    HandoffMessage(
                        source_agent=h_dict.get("source", "unknown"),
                        target_agent=h_dict.get("target", "unknown"),
                        task_description=h_dict.get("task", ""),
                        timestamp=h_dict.get("timestamp", time.time()),
                    )
                )
        return ctx
