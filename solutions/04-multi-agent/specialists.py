"""Specialist agents: ResearchSpecialist and AnalysisSpecialist."""

import json
from typing import Any, Dict, List, Optional

from shared.agent import BaseAgent
from shared.llm_client import BaseLLMClient, get_llm_client
from shared.logging import AgentLogger

try:
    from .schemas import HandoffMessage, SharedContext, AgentRole, AgentState
except ImportError:
    from schemas import HandoffMessage, SharedContext, AgentRole, AgentState

import sys
from pathlib import Path

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
        """Execute a research subtask and record findings in the shared context."""
        self.logger.log("TASK_START", f"Executing research task: '{handoff.task_description}'")

        query = handoff.context_payload.get("query") or handoff.task_description
        limit = handoff.context_payload.get("limit", 4)

        # Retrieve relevant literature using bibliographic tool
        papers = search_papers(query=query, limit=limit)

        # Enhance with full details where necessary
        detailed_papers = []
        for p in papers:
            details = get_paper_details(p["paper_id"])
            detailed_papers.append(details if "error" not in details else p)

        # Update shared context blackboard
        context.retrieved_papers = detailed_papers

        result = {
            "status": "success",
            "papers_found": len(detailed_papers),
            "titles": [p["title"] for p in detailed_papers],
            "top_paper_id": detailed_papers[0]["paper_id"] if detailed_papers else None,
        }
        self.logger.log("TASK_COMPLETE", f"Found {len(detailed_papers)} papers for query '{query}'")
        return result

    def node_function(self, state: AgentState) -> AgentState:
        """LangGraph node execution function for the Research Specialist."""
        query = state.get("query", "")
        self.logger.log("NODE_EXECUTE", f"[LangGraph Node: Researcher] querying literature for: '{query}'")

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
        """Analyze retrieved papers in the shared context and extract methodology comparisons and stats."""
        self.logger.log("TASK_START", f"Executing analysis task: '{handoff.task_description}'")

        papers = context.retrieved_papers or handoff.context_payload.get("papers", [])
        if not papers:
            err = {"error": "No papers available in context to analyze."}
            self.logger.error(str(err))
            return err

        # 1. Aggregate citation metrics using compute_citation_stats tool
        paper_ids = [p["paper_id"] for p in papers if "paper_id" in p]
        stats = compute_citation_stats(paper_ids)

        # 2. Extract structured comparative methodology matrix
        comparisons = []
        for p in papers:
            comparisons.append({
                "title": p.get("title"),
                "year": p.get("year"),
                "citations": p.get("citations", 0),
                "topics": p.get("topics", []),
                "key_contribution": p.get("abstract", "")[:120] + "...",
            })

        # 3. Calculate metrics using calculation tool
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
                f"Paper '{papers[0].get('title')}' is the most cited with {papers[0].get('citations'):,} citations.",
                f"Publication years span {min(p.get('year', 2020) for p in papers)} to {max(p.get('year', 2020) for p in papers)}.",
            ],
        }

        # Store in shared context blackboard
        context.analysis_artifacts = analysis_result

        self.logger.log("TASK_COMPLETE", "Completed comparative analysis and citation modeling.")
        return analysis_result

    def node_function(self, state: AgentState) -> AgentState:
        """LangGraph node execution function for the Analysis Specialist."""
        self.logger.log("NODE_EXECUTE", "[LangGraph Node: Analyst] Computing bibliometrics and methodology matrix")
        papers = state.get("retrieved_papers", [])

        paper_ids = [p["paper_id"] for p in papers if "paper_id" in p]
        stats = compute_citation_stats(paper_ids) if paper_ids else {}

        comparisons = []
        for p in papers:
            comparisons.append({
                "title": p.get("title"),
                "year": p.get("year"),
                "citations": p.get("citations", 0),
                "topics": p.get("topics", []),
                "key_contribution": p.get("abstract", "")[:120] + "...",
            })

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
                f"Paper '{papers[0].get('title')}' is the most cited with {papers[0].get('citations'):,} citations." if papers else "No papers found.",
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
