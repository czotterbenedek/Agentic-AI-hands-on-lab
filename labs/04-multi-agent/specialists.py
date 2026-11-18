"""Specialist agents: ResearchSpecialist and AnalysisSpecialist (Starter Lab)."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.agent import BaseAgent
from shared.llm_client import BaseLLMClient, get_llm_client
from shared.logging import AgentLogger

try:
    from .schemas import HandoffMessage, SharedContext, AgentRole, AgentState
except ImportError:
    from schemas import HandoffMessage, SharedContext, AgentRole, AgentState

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

RESEARCHER_SYSTEM_PROMPT = """You are the Academic Research Specialist Agent dedicated to bibliographic discovery and literature retrieval.

Role & Responsibilities:
1. Search academic paper repositories for topics requested by the Supervisor.
2. Retrieve complete metadata (titles, authors, publication years, citations, abstracts).
3. Filter and rank papers by relevance and academic citation impact.
4. Strictly adhere to academic bibliographic standards (cite paper IDs and DOIs accurately).
5. Output structured literature findings into the shared research state."""


ANALYST_SYSTEM_PROMPT = """You are the Academic Analysis Specialist Agent specializing in comparative literature analysis and bibliometrics.

Role & Responsibilities:
1. Perform quantitative and qualitative analysis on papers provided in the shared research state.
2. Compute citation metrics (total, average, max, citation ratio) using calculation tools.
3. Build comparative methodology matrices contrasting architectures, datasets, and benchmark results.
4. Identify research trends, common limitations, and open academic directions.
5. Return structured analysis artifacts to the Supervisor for final synthesis."""


class ResearchSpecialist(BaseAgent):
    """Specialist responsible for querying academic databases, finding papers, and filtering results."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        verbose: bool = True,
        system_prompt: str = RESEARCHER_SYSTEM_PROMPT,
    ):
        self.role = AgentRole.RESEARCHER
        self.client = llm_client or get_llm_client()
        self.logger = AgentLogger(name="ResearchSpecialist", verbose=verbose)
        self.system_prompt = system_prompt

    def execute_task(self, handoff: HandoffMessage, context: SharedContext) -> Dict[str, Any]:
        """Execute a research subtask and record findings in the shared context.

        # ==============================================================================
        # TODO [Lab 4.1]: Research Specialist Execution (~35 lines)
        # ------------------------------------------------------------------------------
        # When the Supervisor delegates to this specialist:
        # 1. Log task start: `self.logger.log("TASK_START", ...)`.
        # 2. Extract `query` and `limit` from `handoff.context_payload` (or `handoff.task_description`).
        # 3. Call `search_papers(query=query, limit=limit)` to find candidate papers.
        # 4. Enhance each paper with full metadata using `get_paper_details(paper_id)`.
        # 5. Crucial: Write the retrieved detailed papers to the shared blackboard:
        #    `context.retrieved_papers = detailed_papers`.
        # 6. Return a summary dict containing status, papers_found, and titles.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.1]: Implement execute_task")

    def node_function(self, state: AgentState) -> AgentState:
        """LangGraph node execution function wrapping Research Specialist task."""
        query = state.get("query", "")
        papers = search_papers(query=query, limit=4)
        detailed_papers = []
        for p in papers:
            details = get_paper_details(p["paper_id"])
            detailed_papers.append(details if "error" not in details else p)

        handoff_entry = {
            "source": AgentRole.SUPERVISOR.value,
            "target": AgentRole.RESEARCHER.value,
            "task": f"Discovered {len(detailed_papers)} papers for '{query}'",
            "timestamp": __import__("time").time(),
        }
        updated_history = list(state.get("delegation_history", []))
        updated_history.append(handoff_entry)

        return {
            **state,
            "retrieved_papers": detailed_papers,
            "delegation_history": updated_history,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "next_step": "supervisor",
        }

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

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        verbose: bool = True,
        system_prompt: str = ANALYST_SYSTEM_PROMPT,
    ):
        self.role = AgentRole.ANALYST
        self.client = llm_client or get_llm_client()
        self.logger = AgentLogger(name="AnalysisSpecialist", verbose=verbose)
        self.system_prompt = system_prompt

    def execute_task(self, handoff: HandoffMessage, context: SharedContext) -> Dict[str, Any]:
        """Analyze retrieved papers in the shared context and extract methodology comparisons and stats.

        # ==============================================================================
        # TODO [Lab 4.2]: Analysis Specialist Execution (~40 lines)
        # ------------------------------------------------------------------------------
        # 1. Inspect `context.retrieved_papers` (or fallback to handoff payload).
        #    If no papers available, log an error and return an error dict.
        # 2. Extract paper IDs and call `compute_citation_stats(paper_ids)`.
        # 3. Create a comparative methodology matrix from paper titles, years, topics, and abstracts.
        # 4. If at least 2 papers exist, compute top-2 citation ratio using `calculate(...)`.
        # 5. Populate `context.analysis_artifacts` with the resulting dictionary.
        # 6. Return the analysis result dict.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.2]: Implement execute_task")

    def node_function(self, state: AgentState) -> AgentState:
        """LangGraph node execution function wrapping Analysis Specialist task."""
        papers = state.get("retrieved_papers", [])
        paper_ids = [p["paper_id"] for p in papers if "paper_id" in p]
        stats = compute_citation_stats(paper_ids) if paper_ids else {}

        comparisons = [
            {
                "title": p.get("title"),
                "year": p.get("year"),
                "citations": p.get("citations", 0),
                "topics": p.get("topics", []),
                "key_contribution": p.get("abstract", "")[:120] + "...",
            }
            for p in papers
        ]

        ratio_calc = "N/A"
        if len(papers) >= 2 and papers[1].get("citations", 0) > 0:
            c1 = papers[0].get("citations", 0)
            c2 = papers[1].get("citations", 1)
            ratio_calc = calculate(f"{c1} / {c2}")

        analysis_result = {
            "citation_statistics": stats,
            "methodology_matrix": comparisons,
            "citation_ratio_top_two": ratio_calc,
            "synthesis_insights": [
                f"Paper '{papers[0].get('title')}' is top cited with {papers[0].get('citations'):,} citations." if papers else "No papers.",
            ],
        }

        handoff_entry = {
            "source": AgentRole.SUPERVISOR.value,
            "target": AgentRole.ANALYST.value,
            "task": f"Analyzed {len(papers)} papers, citation ratio: {ratio_calc}",
            "timestamp": __import__("time").time(),
        }
        updated_history = list(state.get("delegation_history", []))
        updated_history.append(handoff_entry)

        return {
            **state,
            "analysis_artifacts": analysis_result,
            "delegation_history": updated_history,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "next_step": "supervisor",
        }

    def run(self, user_query: str, **kwargs: Any) -> str:
        ctx = SharedContext(raw_query=user_query)
        msg = HandoffMessage(
            source_agent="user",
            target_agent=self.role.value,
            task_description=user_query,
        )
        res = self.execute_task(msg, ctx)
        return json.dumps(res, indent=2)
