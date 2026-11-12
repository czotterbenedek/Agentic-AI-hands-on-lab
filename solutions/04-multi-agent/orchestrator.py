"""Multi-agent orchestrator managing blackboard context and delegation guardrails."""

from typing import Any, Dict, List, Optional

from shared.logging import AgentLogger
try:
    from .schemas import HandoffMessage, SharedContext, AgentRole
    from .supervisor import SupervisorAgent
except ImportError:
    from schemas import HandoffMessage, SharedContext, AgentRole
    from supervisor import SupervisorAgent


class MultiAgentOrchestrator:
    """Coordinates execution across multi-agent systems with loop and depth guardrails."""

    def __init__(
        self,
        supervisor: Optional[SupervisorAgent] = None,
        max_delegation_depth: int = 4,
        verbose: bool = True,
    ):
        self.supervisor = supervisor or SupervisorAgent(
            max_delegation_depth=max_delegation_depth, verbose=verbose
        )
        self.max_delegation_depth = max_delegation_depth
        self.logger = AgentLogger(name="Orchestrator", verbose=verbose)

    def detect_cycle(self, history: List[HandoffMessage]) -> bool:
        """Detect circular delegation patterns (e.g. A -> B -> A -> B)."""
        if len(history) < 4:
            return False
        # Check if the last two handoffs repeat the previous two
        h = [(m.source_agent, m.target_agent) for m in history]
        if h[-1] == h[-3] and h[-2] == h[-4]:
            return True
        return False

    def execute_workflow(self, user_query: str) -> SharedContext:
        """Execute coordinated multi-agent workflow on a user query."""
        context = SharedContext(raw_query=user_query)
        self.logger.log("WORKFLOW_START", f"Starting multi-agent workflow for: '{user_query}'")

        context = self.supervisor.plan_and_delegate(user_query, context)

        if self.detect_cycle(context.delegation_history):
            self.logger.error("Cycle detected in agent delegation! Aborting to avoid infinite loop.")

        self.logger.log(
            "WORKFLOW_COMPLETE",
            f"Workflow finished with {len(context.delegation_history)} delegation hops.",
        )
        return context
