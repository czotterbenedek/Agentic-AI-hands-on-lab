"""Supervisor agent responsible for decomposing research tasks and orchestrating specialist handoffs."""

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
        """Decompose query into specialized steps and execute handoffs with guardrails."""
        self.logger.log("PLAN", f"Analyzing user query: '{user_query}'")

        # Guardrail check: max delegation depth
        if len(context.delegation_history) >= self.max_delegation_depth:
            self.logger.error("Delegation limit reached. Aborting further handoffs.")
            return context

        # ----------------------------------------------------------------------
        # Handoff 1: Supervisor -> Research Specialist
        # ----------------------------------------------------------------------
        research_handoff = HandoffMessage(
            source_agent=self.role.value,
            target_agent=AgentRole.RESEARCHER.value,
            task_description=f"Find key academic literature for: {user_query}",
            context_payload={"query": user_query, "limit": 4},
        )
        self.logger.handoff(
            self.role.value, AgentRole.RESEARCHER.value, research_handoff.task_description
        )
        context.record_handoff(research_handoff)

        self.researcher.execute_task(research_handoff, context)

        # ----------------------------------------------------------------------
        # Handoff 2: Supervisor -> Analysis Specialist
        # ----------------------------------------------------------------------
        analysis_handoff = HandoffMessage(
            source_agent=self.role.value,
            target_agent=AgentRole.ANALYST.value,
            task_description="Perform comparative analysis, methodology comparison, and compute citation statistics",
            context_payload={"papers": context.retrieved_papers},
        )
        self.logger.handoff(
            self.role.value, AgentRole.ANALYST.value, analysis_handoff.task_description
        )
        context.record_handoff(analysis_handoff)

        self.analyst.execute_task(analysis_handoff, context)

        # ----------------------------------------------------------------------
        # Final Synthesis by Supervisor
        # ----------------------------------------------------------------------
        context.final_synthesis = self.synthesize_report(context)
        return context

    def synthesize_report(self, context: SharedContext) -> str:
        """Synthesize findings from both specialists into an executive academic literature report."""
        papers = context.retrieved_papers
        analysis = context.analysis_artifacts
        stats = analysis.get("citation_statistics", {})
        matrix = analysis.get("methodology_matrix", [])

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
