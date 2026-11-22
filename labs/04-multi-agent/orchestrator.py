"""Multi-agent orchestrator managing LangGraph StateGraph, conditional edges, and cycle guardrails (Starter Lab)."""

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

                state = node_fn(state)
                self.checkpointer.put(thread_id, state)

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
        self.app = self._build_langgraph()

    def _build_langgraph(self) -> Any:
        """Construct and compile the LangGraph multi-agent StateGraph.

        # ==============================================================================
        # TODO [Lab 4.4]: Build LangGraph Multi-Agent StateGraph (~30 lines)
        # ------------------------------------------------------------------------------
        # 1. Initialize `workflow = StateGraph(AgentState)`.
        # 2. Add nodes:
        #    - "supervisor": `self.supervisor.node_function`
        #    - "researcher": `self.supervisor.researcher.node_function`
        #    - "analyst": `self.supervisor.analyst.node_function`
        # 3. Add conditional edge from "supervisor" using `route_supervisor_decision`
        #    mapping: {"researcher": "researcher", "analyst": "analyst", "finish": END}.
        # 4. Add return edges:
        #    - "researcher" -> "supervisor"
        #    - "analyst" -> "supervisor"
        # 5. Set entry point to "supervisor".
        # 6. Return compiled workflow: `workflow.compile(checkpointer=self.checkpointer)`.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.4]: Implement _build_langgraph")

    def detect_cycle(self, history: List[Any]) -> bool:
        """Detect circular delegation patterns (e.g. A -> B -> A -> B).

        # ==============================================================================
        # TODO [Lab 4.5a]: Delegation Cycle Detection (~20 lines)
        # ------------------------------------------------------------------------------
        # If an agent loop gets stuck delegating back and forth between two agents:
        # 1. If `len(history) < 4`, return False.
        # 2. Extract (source, target) tuples for each handoff item.
        # 3. Check if `hops[-1] == hops[-3]` and `hops[-2] == hops[-4]`.
        # 4. If matching, return True (cycle detected!), else False.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.5a]: Implement detect_cycle")

    def execute_workflow(self, user_query: str) -> SharedContext:
        """Execute coordinated multi-agent workflow on a user query using LangGraph.

        # ==============================================================================
        # TODO [Lab 4.5b]: LangGraph Execution Harness (~25 lines)
        # ------------------------------------------------------------------------------
        # 1. Prepare initial `AgentState` with query, empty lists/dicts, and next_step="supervisor".
        # 2. Configure thread_id and recursion_limit in config dict.
        # 3. Invoke compiled graph: `final_state = self.app.invoke(initial_state, config=config)`.
        # 4. Check for cycles in `final_state['delegation_history']`.
        # 5. Convert final state to SharedContext: `SharedContext.from_agent_state(final_state)`.
        # 6. Return context.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 4.5b]: Implement execute_workflow")

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run workflow and return final synthesized report."""
        context = self.execute_workflow(user_query)
        return context.final_synthesis or "Synthesis failed."
