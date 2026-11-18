"""Supervisor agent responsible for decomposing research tasks and orchestrating specialist handoffs (Starter Lab)."""

import json
from typing import Any, Dict, List, Optional

from shared.agent import BaseAgent
from shared.llm_client import BaseLLMClient, get_llm_client
from shared.logging import AgentLogger

try:
    from .schemas import HandoffMessage, SharedContext, AgentRole, AgentState
    from .specialists import ResearchSpecialist, AnalysisSpecialist
except ImportError:
    from schemas import HandoffMessage, SharedContext, AgentRole, AgentState
    from specialists import ResearchSpecialist, AnalysisSpecialist

SUPERVISOR_SYSTEM_PROMPT = """You are the Academic Research Supervisor Agent orchestrating a team of specialist AI agents in a LangGraph state workflow.

Your role is to coordinate the research lifecycle to address graduate-level academic inquiries.

Your Team Members:
1. 'researcher' (Research Specialist): Queries academic paper databases, retrieves arXiv/bibliographic records, and extracts relevant literature.
2. 'analyst' (Analysis Specialist): Analyzes methodology, performs comparative study, and calculates citation statistics across retrieved papers.

Supervisor Responsibilities:
- Deconstruct complex academic questions into clear, actionable subtasks for specialists.
- Delegate first to 'researcher' if relevant papers have not yet been retrieved.
- Delegate next to 'analyst' once papers are collected to compute citation metrics and compare architectures.
- Halt further delegation ('finish') once sufficient literature and quantitative analysis are gathered.
- Synthesize an executive report featuring Literature Review, Quantitative Comparison, and Methodological Insights."""


class SupervisorAgent(BaseAgent):
    """Supervisor agent that coordinates research and analysis specialists to produce synthesized reports."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        max_delegation_depth: int = 4,
        verbose: bool = True,
        system_prompt: str = SUPERVISOR_SYSTEM_PROMPT,
    ):
        self.role = AgentRole.SUPERVISOR
        self.client = llm_client or get_llm_client()
        self.max_delegation_depth = max_delegation_depth
        self.logger = AgentLogger(name="SupervisorAgent", verbose=verbose)
        self.system_prompt = system_prompt
        self.researcher = ResearchSpecialist(llm_client=self.client, verbose=verbose)
        self.analyst = AnalysisSpecialist(llm_client=self.client, verbose=verbose)

    def plan_and_delegate(self, user_query: str, context: SharedContext) -> SharedContext:
        """Decompose query into specialized steps and execute handoffs with guardrails.

        # ==============================================================================
        # TODO [Lab 4.3]: Supervisor Task Decomposition & Delegation (~45 lines)
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
        raise NotImplementedError("TODO [Lab 4.3]: Implement plan_and_delegate")

    def node_function(self, state: AgentState) -> AgentState:
        """LangGraph node execution function for the Supervisor Agent."""
        iter_count = state.get("iteration_count", 0)
        if iter_count >= self.max_delegation_depth:
            final_report = self.synthesize_from_state(state)
            return {**state, "next_step": "finish", "final_report": final_report}

        if not state.get("retrieved_papers"):
            return {**state, "next_step": "researcher"}

        if not state.get("analysis_artifacts"):
            return {**state, "next_step": "analyst"}

        final_report = self.synthesize_from_state(state)
        return {**state, "next_step": "finish", "final_report": final_report}

    def synthesize_from_state(self, state: AgentState) -> str:
        """Synthesize report directly from LangGraph AgentState dictionary."""
        ctx = SharedContext(
            raw_query=state.get("query", ""),
            retrieved_papers=state.get("retrieved_papers", []),
            analysis_artifacts=state.get("analysis_artifacts", {}),
        )
        return self.synthesize_report(ctx)

    def synthesize_report(self, context: SharedContext) -> str:
        """Synthesize findings from both specialists into an executive academic literature report."""
        papers = context.retrieved_papers
        analysis = context.analysis_artifacts
        stats = analysis.get("citation_statistics", {})

        report_lines = [
            "# Academic Literature Review & Synthesis",
            f"**Research Query:** {context.raw_query}\n",
            "## 1. Literature Discovery (Research Specialist)",
            f"Identified {len(papers)} key research publications:",
        ]

        for p in papers:
            authors_str = ", ".join(p.get("authors", []))
            report_lines.append(
                f"- **{p.get('title')}** ({p.get('year')}) — {authors_str}\n"
                f"  *Citations:* {p.get('citations', 0):,} | *Topics:* {', '.join(p.get('topics', []))}"
            )

        report_lines.extend([
            "\n## 2. Quantitative & Comparative Analysis (Analysis Specialist)",
            f"- **Total Citations Across Papers:** {stats.get('total_citations', 0):,}",
            f"- **Average Citations Per Paper:** {stats.get('average_citations', 0):,}",
            f"- **Top-2 Citation Ratio:** {analysis.get('citation_ratio_top_two', 'N/A')}",
            "\n### Key Insights:",
        ])

        for insight in analysis.get("synthesis_insights", []):
            report_lines.append(f"• {insight}")

        report_lines.extend([
            "\n## 3. Executive Synthesis & Next Steps",
            "The findings show strong synergy between foundational transformer architectures and "
            "recent parameter-efficient adaptation methods. Further experimental evaluation is recommended.",
        ])

        final_text = "\n".join(report_lines)
        self.logger.final_answer("Supervisor report synthesis complete.")
        return final_text

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run end-to-end multi-agent research workflow on user query."""
        context = SharedContext(raw_query=user_query)
        self.plan_and_delegate(user_query, context)
        return context.final_synthesis or "Synthesis failed."
