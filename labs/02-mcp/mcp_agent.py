"""Research Agent connected to tools exposed via Model Context Protocol (MCP) (Starter Lab)."""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Optional

from shared.agent import BaseAgent
from shared.llm_client import BaseLLMClient, get_llm_client
from shared.logging import AgentLogger

try:
    from .client import MCPClient
    from .server import ResearchMCPServer
except ImportError:
    from client import MCPClient
    from server import ResearchMCPServer


def _load_lab01():
    current_dir = Path(__file__).resolve().parent
    base_dir = current_dir.parent / "01-tool-calling"
    if not (base_dir / "react_agent.py").exists():
        base_dir = current_dir.parent.parent / "solutions" / "01-tool-calling"

    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    agent_path = base_dir / "react_agent.py"
    tools_path = base_dir / "tools.py"

    spec_tools = importlib.util.spec_from_file_location("tools_mod", tools_path)
    tools_mod = importlib.util.module_from_spec(spec_tools)
    spec_tools.loader.exec_module(tools_mod)

    spec_agent = importlib.util.spec_from_file_location("agent_mod", agent_path)
    agent_mod = importlib.util.module_from_spec(spec_agent)
    spec_agent.loader.exec_module(agent_mod)

    return agent_mod.ReActAgent, tools_mod.ToolRegistry


ReActAgent, ToolRegistry = _load_lab01()

MCP_SYSTEM_PROMPT = """You are the University Research Assistant connected to specialized bibliographic tools via the Model Context Protocol (MCP).

Your responsibility is to assist researchers and graduate students in exploring academic literature, discovering recent publications, retrieving paper details, and analyzing research findings.

Protocol Rules & Constraints:
1. Always utilize the discovered MCP tools (search_papers, get_paper_details, get_recent_papers) to query bibliographic metadata.
2. Provide exact paper identifiers (arXiv IDs, DOIs), author lists, and publication years in your synthesis.
3. If an MCP tool returns an error or no matches, communicate the error transparently and suggest query refinements.
4. Summarize literature objectively and highlight key architectural or theoretical contributions."""


class MCPAgent(BaseAgent):
    """University Research Assistant powered by MCP-discovered tools."""

    def __init__(
        self,
        mcp_client: Optional[MCPClient] = None,
        llm_client: Optional[BaseLLMClient] = None,
        verbose: bool = True,
        system_prompt: str = MCP_SYSTEM_PROMPT,
    ):
        self.client = llm_client or get_llm_client()
        self.logger = AgentLogger(name="MCPAgent", verbose=verbose)
        self.system_prompt = system_prompt
        if mcp_client is None:
            # Default to in-memory research MCP server for instant startup
            server = ResearchMCPServer()
            self.mcp_client = MCPClient(in_memory_server=server)
        else:
            self.mcp_client = mcp_client

        self.mcp_client.connect()
        self.tool_registry = ToolRegistry()
        self._load_mcp_tools()

        # ==============================================================================
        # TODO [Lab 2.5]: Instantiate the ReActAgent with MCP tools (~6 lines)
        # ------------------------------------------------------------------------------
        # Create `self.react_agent` by instantiating `ReActAgent` with:
        #   - llm_client  : self.client
        #   - tool_registry: self.tool_registry  (already populated by _load_mcp_tools)
        #   - verbose     : verbose
        #   - system_prompt: self.system_prompt
        # ==============================================================================
        raise NotImplementedError("TODO [Lab 2.5]: Instantiate self.react_agent = ReActAgent(...)")

    def _load_mcp_tools(self) -> None:
        """Discover tools from MCP server and register them in agent registry.

        # ==============================================================================
        # TODO [Lab 2.4]: MCP Tool Discovery and Agent Registration (~5 lines)
        # ------------------------------------------------------------------------------
        # Connect discovered MCP capabilities to the agent's ToolRegistry:
        #
        # 1. Call `self.mcp_client.to_agent_tools()` to obtain converted `Tool` instances.
        # 2. For each tool `t` in the returned list:
        #    Add it to the registry: `self.tool_registry._tools[t.name] = t`
        # 3. Log the discovered tool names: `self.logger.log("INIT", ...)`
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.4]: Implement _load_mcp_tools")

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run the research agent with MCP tools."""
        return self.react_agent.run(user_query)
