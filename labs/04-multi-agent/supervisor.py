"""Supervisor agent responsible for decomposing research tasks and orchestrating specialist handoffs (Starter Lab)."""

import json
from typing import Any, Dict, List, Optional

from shared.agent import BaseAgent
from shared.llm_client import BaseLLMClient, get_llm_client
from shared.logging import AgentLogger

try:
    from .schemas import HandoffMessage, SharedContext, AgentRole
    from .specialists import ResearchSpecialist, AnalysisSpecialist
except ImportError:
    from schemas import HandoffMessage, SharedContext, AgentRole
    from specialists import ResearchSpecialist, AnalysisSpecialist


class SupervisorAgent(BaseAgent):
    """Supervisor agent that coordinates research and analysis specialists to produce synthesized reports."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        max_delegation_depth: int = 4,
        verbose: bool = True,
    ):
        self.role = AgentRole.SUPERVISOR
        self.client = llm_client or get_llm_client()
        self.max_delegation_depth = max_delegation_depth
        self.logger = AgentLogger(name="SupervisorAgent", verbose=verbose)
        self.researcher = ResearchSpecialist(llm_client=self.client, verbose=verbose)
        self.analyst = AnalysisSpecialist(llm_client=self.client, verbose=verbose)

    def plan_and_delegate(self, user_query: str, context: SharedContext) -> SharedContext:
        """Decompose query into specialized steps and execute handoffs with guardrails.

        # ==============================================================================
        # TODO [Lab 4.3]: Supervisor Task Decomposition & Delegation (~55 lines)
        # ------------------------------------------------------------------------------
        # Implement multi-agent orchestration with guardrails:
        #
        # 1. Guardrail check: if `len(context.delegation_history) >= self.max_delegation_depth`:
        #    Log error and return context immediately (prevents infinite delegation loops!).
        # 2. Step 1 (Research Handoff):
        #    - Create `HandoffMessage` from supervisor to "researcher" with task description
        #      and payload `{"query": user_query, "limit": 4}`.
        #    - Log handoff: `self.logger.handoff(...)`.
        #    - Record handoff in `context.record_handoff(...)`.
        #    - Execute: call `self.researcher.execute_task(research_handoff, context)`.
        # 3. Step 2 (Analysis Handoff):
        #    - Create `HandoffMessage` from supervisor to "analyst" with payload passing
        #      the retrieved papers.
        #    - Log handoff and record in context.
        #    - Execute: call `self.analyst.execute_task(analysis_handoff, context)`.
        # 4. Step 3 (Report Synthesis):
        #    - Synthesize final review using `self.synthesize_report(context)`.
        #    - Store in `context.final_synthesis`.
        # 5. Return context.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.3]: Implement SupervisorAgent.plan_and_delegate")

    def synthesize_report(self, context: SharedContext) -> str:
        """Synthesize findings from both specialists into an executive academic literature report.

        # ==============================================================================
        # TODO [Lab 4.4]: Supervisor Synthesis Report (~40 lines)
        # ------------------------------------------------------------------------------
        # Compile a cohesive literature review from the shared context:
        # 1. Extract papers from `context.retrieved_papers`.
        # 2. Extract stats and methodology matrix from `context.analysis_artifacts`.
        # 3. Format structured markdown report:
        #    - Section 1: Literature Discovery (list titles, years, authors, citations, topics)
        #    - Section 2: Quantitative Analysis (total citations, average citations, ratio, insights)
        #    - Section 3: Executive Synthesis & Next Steps
        # 4. Log final answer: `self.logger.final_answer(...)`.
        # 5. Return formatted string.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.4]: Implement SupervisorAgent.synthesize_report")

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run end-to-end multi-agent research workflow on user query."""
        context = SharedContext(raw_query=user_query)
        self.plan_and_delegate(user_query, context)
        return context.final_synthesis or "Synthesis failed."
