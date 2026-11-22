"""Multi-agent orchestrator managing LangGraph StateGraph, conditional edges, and cycle guardrails."""

import time
from typing import Any, Callable, Dict, List, Optional

from shared.logging import AgentLogger

try:
    from .schemas import HandoffMessage, SharedContext, AgentRole, AgentState
    from .supervisor import SupervisorAgent
    from .specialists import ResearchSpecialist, AnalysisSpecialist
except ImportError:
    from schemas import HandoffMessage, SharedContext, AgentRole, AgentState
    from supervisor import SupervisorAgent
    from specialists import ResearchSpecialist, AnalysisSpecialist

# ------------------------------------------------------------------------------
# LangGraph Core Import with Embedded Compatible Fallback
# ------------------------------------------------------------------------------
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    HAS_LANGGRAPH_PKG = True
except ImportError:
    HAS_LANGGRAPH_PKG = False
    END = "__end__"

    class MemorySaver:
        """In-memory checkpointer saving graph snapshots per thread ID."""
        def __init__(self):
            self.storage: Dict[str, List[Dict[str, Any]]] = {}

        def put(self, thread_id: str, state: Dict[str, Any]) -> None:
            self.storage.setdefault(thread_id, []).append(dict(state))

        def get(self, thread_id: str) -> Dict[str, Any]:
            history = self.storage.get(thread_id, [])
            return dict(history[-1]) if history else {}

    class CompiledGraph:
        """Compiled execution engine for StateGraph."""
        def __init__(self, graph: "StateGraph", checkpointer: Optional[MemorySaver] = None):
            self.graph = graph
            self.checkpointer = checkpointer or MemorySaver()

        def invoke(self, initial_state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            thread_id = (config or {}).get("configurable", {}).get("thread_id", "default")
            recursion_limit = (config or {}).get("recursion_limit", 15)

            current_node = self.graph.entry_point
            state = dict(initial_state)
            steps = 0

            while current_node and current_node != END and steps < recursion_limit:
                steps += 1
                node_fn = self.graph.nodes.get(current_node)
                if not node_fn:
                    break

                # Execute node function
                state = node_fn(state)
                self.checkpointer.put(thread_id, state)

                # Determine next node via conditional edges or standard edge
                if current_node in self.graph.conditional_edges:
                    routing_fn, path_map = self.graph.conditional_edges[current_node]
                    route_decision = routing_fn(state)
                    current_node = path_map.get(route_decision, END)
                elif current_node in self.graph.edges:
                    current_node = self.graph.edges[current_node]
                else:
                    current_node = END

            return state

    class StateGraph:
        """LangGraph-compatible StateGraph constructing workflow nodes and edges."""
        def __init__(self, state_schema: Any):
            self.state_schema = state_schema
            self.nodes: Dict[str, Callable[[Any], Any]] = {}
            self.edges: Dict[str, str] = {}
            self.conditional_edges: Dict[str, Any] = {}
            self.entry_point: Optional[str] = None

        def add_node(self, name: str, func: Callable[[Any], Any]) -> None:
            self.nodes[name] = func

        def add_edge(self, source: str, target: str) -> None:
            self.edges[source] = target

        def add_conditional_edges(
            self, source: str, routing_fn: Callable[[Any], str], path_map: Dict[str, str]
        ) -> None:
            self.conditional_edges[source] = (routing_fn, path_map)

        def set_entry_point(self, name: str) -> None:
            self.entry_point = name

        def compile(self, checkpointer: Optional[Any] = None) -> CompiledGraph:
            return CompiledGraph(self, checkpointer=checkpointer)


def route_supervisor_decision(state: AgentState) -> str:
    """Conditional routing function determining the next step from supervisor state."""
    # Active cycle detection during graph routing
    history = state.get("delegation_history", [])
    if len(history) >= 4:
        hops = []
        for h in history:
            if isinstance(h, dict):
                hops.append((h.get("source"), h.get("target")))
        if len(hops) >= 4 and hops[-1] == hops[-3] and hops[-2] == hops[-4]:
            return "finish"

    next_step = state.get("next_step", "finish")
    if next_step == "researcher":
        return "researcher"
    elif next_step == "analyst":
        return "analyst"
    return "finish"


class MultiAgentOrchestrator:
    """Coordinates execution across multi-agent systems using LangGraph StateGraph."""

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
        self.checkpointer = MemorySaver()

        # Build compiled LangGraph workflow
        self.app = self._build_langgraph()

    def _build_langgraph(self) -> Any:
        """Construct and compile the LangGraph multi-agent StateGraph."""
        self.logger.log("BUILD", "Compiling LangGraph StateGraph with supervisor and specialist nodes...")
        workflow = StateGraph(AgentState)

        # 1. Add Graph Nodes
        workflow.add_node("supervisor", self.supervisor.node_function)
        workflow.add_node("researcher", self.supervisor.researcher.node_function)
        workflow.add_node("analyst", self.supervisor.analyst.node_function)

        # 2. Add Conditional Routing Edge from Supervisor
        workflow.add_conditional_edges(
            "supervisor",
            route_supervisor_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "finish": END,
            },
        )

        # 3. Add Edges returning back to Supervisor for evaluation and synthesis
        workflow.add_edge("researcher", "supervisor")
        workflow.add_edge("analyst", "supervisor")

        # 4. Set Entry Point and Compile with Checkpointer
        workflow.set_entry_point("supervisor")
        return workflow.compile(checkpointer=self.checkpointer)

    def detect_cycle(self, history: List[Any]) -> bool:
        """Detect circular delegation patterns (e.g. A -> B -> A -> B)."""
        if len(history) < 4:
            return False

        # Extract (source, target) tuples
        hops = []
        for h in history:
            if isinstance(h, HandoffMessage):
                hops.append((h.source_agent, h.target_agent))
            elif isinstance(h, dict):
                hops.append((h.get("source"), h.get("target")))

        if len(hops) >= 4 and hops[-1] == hops[-3] and hops[-2] == hops[-4]:
            return True
        return False

    def execute_workflow(self, user_query: str) -> SharedContext:
        """Execute coordinated multi-agent workflow on a user query using LangGraph."""
        self.logger.log("WORKFLOW_START", f"Starting LangGraph workflow for: '{user_query}'")

        initial_state: AgentState = {
            "query": user_query,
            "messages": [],
            "retrieved_papers": [],
            "analysis_artifacts": {},
            "next_step": "supervisor",
            "iteration_count": 0,
            "delegation_history": [],
            "final_report": None,
        }

        thread_id = f"thread_{int(time.time() * 1000)}"
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": self.max_delegation_depth * 3,
        }

        # Run compiled LangGraph
        final_state = self.app.invoke(initial_state, config=config)

        # Safeguard: check for cyclic delegation
        if self.detect_cycle(final_state.get("delegation_history", [])):
            self.logger.error("Cycle detected in agent delegation! Aborting to avoid infinite loop.")

        # Convert resulting state back to SharedContext
        context = SharedContext.from_agent_state(final_state)
        self.logger.log(
            "WORKFLOW_COMPLETE",
            f"LangGraph workflow finished with {len(context.delegation_history)} delegation hops.",
        )
        return context

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run workflow and return final synthesized report."""
        context = self.execute_workflow(user_query)
        return context.final_synthesis or "Synthesis failed."
