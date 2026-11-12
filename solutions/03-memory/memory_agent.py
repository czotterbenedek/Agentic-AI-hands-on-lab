"""Research Assistant Agent augmented with persistent SQLite memory."""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Optional

from shared.agent import BaseAgent
from shared.llm_client import BaseLLMClient, get_llm_client
from shared.logging import AgentLogger

try:
    from .storage import SQLiteMemoryStorage
    from .memory_manager import MemoryManager
except ImportError:
    from storage import SQLiteMemoryStorage
    from memory_manager import MemoryManager


def _load_lab01():
    current_dir = Path(__file__).resolve().parent
    base_dir = current_dir.parent / "01-tool-calling"
    if not (base_dir / "react_agent.py").exists():
        base_dir = current_dir.parent.parent / "solutions" / "01-tool-calling"

    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    agent_path = base_dir / "react_agent.py"
    tools_path = base_dir / "tools.py"

    spec_tools = importlib.util.spec_from_file_location("tools_mod_m", tools_path)
    tools_mod = importlib.util.module_from_spec(spec_tools)
    spec_tools.loader.exec_module(tools_mod)

    spec_agent = importlib.util.spec_from_file_location("agent_mod_m", agent_path)
    agent_mod = importlib.util.module_from_spec(spec_agent)
    spec_agent.loader.exec_module(agent_mod)

    return agent_mod.ReActAgent, tools_mod.get_default_tool_registry


ReActAgent, get_default_tool_registry = _load_lab01()


class MemoryAugmentedAgent(BaseAgent):
    """University Research Assistant with short-term history and persistent user memory."""

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        llm_client: Optional[BaseLLMClient] = None,
        verbose: bool = True,
    ):
        self.client = llm_client or get_llm_client()
        self.memory = memory_manager or MemoryManager()
        self.logger = AgentLogger(name="MemoryAgent", verbose=verbose)
        self.verbose = verbose

    def run(
        self,
        user_query: str,
        user_id: str = "student_default",
        session_id: str = "session_default",
        **kwargs: Any,
    ) -> str:
        """Run agent on user query with persistent context injection and turn recording."""
        # 1. Retrieve persistent memory context (preferences and notes)
        memory_context = self.memory.get_system_context(user_id)

        # 2. Prepare tool registry with research tools + memory tools
        registry = get_default_tool_registry()
        for t in self.memory.get_memory_tools(user_id):
            registry._tools[t.name] = t

        # 3. Build dynamic prompt
        base_system = (
            "You are the University Research Assistant, an intelligent academic agent.\n"
            "You have access to bibliographic tools and persistent memory tools."
        )
        if memory_context:
            full_prompt = f"{base_system}\n\n{memory_context}"
        else:
            full_prompt = base_system

        # 4. Instantiate and run ReAct agent
        agent = ReActAgent(
            llm_client=self.client,
            tool_registry=registry,
            system_prompt=full_prompt,
            verbose=self.verbose,
        )

        # Preload recent short-term conversation turns
        recent_turns = self.memory.get_recent_history(user_id, session_id)
        for turn in recent_turns:
            agent.messages.append(
                agent.client.__class__  # type ignore
            ) if False else None

        # Execute
        answer = agent.run(user_query)

        # 5. Record this conversation turn in persistent storage
        self.memory.record_turn(user_id, session_id, "user", user_query)
        self.memory.record_turn(user_id, session_id, "assistant", answer)

        return answer
