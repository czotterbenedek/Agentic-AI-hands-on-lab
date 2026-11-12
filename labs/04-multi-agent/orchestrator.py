"""Multi-agent orchestrator managing blackboard context and delegation guardrails (Starter Lab)."""

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
        """Detect circular delegation patterns (e.g. A -> B -> A -> B).

        # ==============================================================================
        # TODO [Lab 4.5a]: Delegation Cycle Detection (~20 lines)
        # ------------------------------------------------------------------------------
        # If an agent loop gets stuck delegating back and forth between two agents,
        # it causes infinite token usage:
        # 1. If `len(history) < 4`, return False.
        # 2. Extract pairs of `(source_agent, target_agent)` for each handoff.
        # 3. Check if `history[-1] == history[-3]` and `history[-2] == history[-4]`.
        # 4. If matching, return True (cycle detected!), else False.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.5a]: Implement detect_cycle")

    def execute_workflow(self, user_query: str) -> SharedContext:
        """Execute coordinated multi-agent workflow on a user query.

        # ==============================================================================
        # TODO [Lab 4.5b]: Workflow Execution Harness (~20 lines)
        # ------------------------------------------------------------------------------
        # 1. Initialize `SharedContext(raw_query=user_query)`.
        # 2. Log workflow start.
        # 3. Call `self.supervisor.plan_and_delegate(user_query, context)`.
        # 4. Check for cycles with `self.detect_cycle(context.delegation_history)`.
        # 5. Log workflow completion and return context.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.5b]: Implement execute_workflow")
