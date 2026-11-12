"""Specialist agents: ResearchSpecialist and AnalysisSpecialist (Starter Lab)."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.agent import BaseAgent
from shared.llm_client import BaseLLMClient, get_llm_client
from shared.logging import AgentLogger

try:
    from .schemas import HandoffMessage, SharedContext, AgentRole
except ImportError:
    from schemas import HandoffMessage, SharedContext, AgentRole

# Load tools from 01-tool-calling
def _load_tools():
    current_dir = Path(__file__).resolve().parent
    base_dir = current_dir.parent / "01-tool-calling"
    if not (base_dir / "tools.py").exists():
        base_dir = current_dir.parent.parent / "solutions" / "01-tool-calling"
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    import importlib.util
    tools_path = base_dir / "tools.py"
    spec = importlib.util.spec_from_file_location("tools_for_specialists", tools_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return (
        mod.calculate,
        mod.search_papers,
        mod.get_paper_details,
        mod.compute_citation_stats,
    )

calculate, search_papers, get_paper_details, compute_citation_stats = _load_tools()


class ResearchSpecialist(BaseAgent):
    """Specialist responsible for querying academic databases, finding papers, and filtering results."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None, verbose: bool = True):
        self.role = AgentRole.RESEARCHER
        self.client = llm_client or get_llm_client()
        self.logger = AgentLogger(name="ResearchSpecialist", verbose=verbose)

    def execute_task(self, handoff: HandoffMessage, context: SharedContext) -> Dict[str, Any]:
        """Execute a research subtask and record findings in the shared context.

        # ==============================================================================
        # TODO [Lab 4.1]: Research Specialist Execution (~45 lines)
        # ------------------------------------------------------------------------------
        # When the Supervisor delegates to this specialist:
        # 1. Log task start: `self.logger.log("TASK_START", ...)`.
        # 2. Extract `query` and `limit` from `handoff.context_payload` (or `handoff.task_description`).
        # 3. Call `search_papers(query=query, limit=limit)` to find candidate papers.
        # 4. Enhance each paper with full metadata using `get_paper_details(paper_id)`.
        # 5. Crucial: Write the retrieved detailed papers to the shared blackboard:
        #    `context.retrieved_papers = detailed_papers`.
        # 6. Log task completion: `self.logger.log("TASK_COMPLETE", ...)`.
        # 7. Return a summary dictionary containing status, papers_found, titles, and top_paper_id.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.1]: Implement ResearchSpecialist.execute_task")

    def run(self, user_query: str, **kwargs: Any) -> str:
        ctx = SharedContext(raw_query=user_query)
        msg = HandoffMessage(
            source_agent="user",
            target_agent=self.role.value,
            task_description=user_query,
        )
        res = self.execute_task(msg, ctx)
        return json.dumps(res, indent=2)


class AnalysisSpecialist(BaseAgent):
    """Specialist responsible for comparative analysis, methodology evaluation, and mathematical synthesis."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None, verbose: bool = True):
        self.role = AgentRole.ANALYST
        self.client = llm_client or get_llm_client()
        self.logger = AgentLogger(name="AnalysisSpecialist", verbose=verbose)

    def execute_task(self, handoff: HandoffMessage, context: SharedContext) -> Dict[str, Any]:
        """Analyze retrieved papers in the shared context and extract methodology comparisons and stats.

        # ==============================================================================
        # TODO [Lab 4.2]: Analysis Specialist Execution (~50 lines)
        # ------------------------------------------------------------------------------
        # When receiving papers retrieved by the Research Specialist:
        # 1. Inspect `context.retrieved_papers` (or payload). If empty, log error and return error dict.
        # 2. Extract paper IDs and call `compute_citation_stats(paper_ids)`.
        # 3. Build a structured `methodology_matrix` comparing title, year, citations, topics,
        #    and abstract contribution preview for each paper.
        # 4. If at least 2 papers exist, use `calculate(...)` to compute the citation ratio
        #    between the top 2 papers: `calculate(f"{c1} / {c2}")`.
        # 5. Extract synthesis insights (e.g. most cited paper, publication span).
        # 6. Write the structured results into `context.analysis_artifacts`.
        # 7. Return the analysis result dictionary.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.2]: Implement AnalysisSpecialist.execute_task")

    def run(self, user_query: str, **kwargs: Any) -> str:
        ctx = SharedContext(raw_query=user_query)
        msg = HandoffMessage(
            source_agent="user",
            target_agent=self.role.value,
            task_description=user_query,
        )
        res = self.execute_task(msg, ctx)
        return json.dumps(res, indent=2)
