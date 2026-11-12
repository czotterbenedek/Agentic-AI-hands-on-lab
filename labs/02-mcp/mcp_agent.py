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
    # Look for 01-tool-calling in current parent (e.g. labs or solutions)
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


class MCPAgent(BaseAgent):
    """University Research Assistant powered by MCP-discovered tools."""

    def __init__(
        self,
        mcp_client: Optional[MCPClient] = None,
        llm_client: Optional[BaseLLMClient] = None,
        verbose: bool = True,
    ):
        self.client = llm_client or get_llm_client()
        self.logger = AgentLogger(name="MCPAgent", verbose=verbose)
        if mcp_client is None:
            # Default to in-memory research MCP server for instant startup
            server = ResearchMCPServer()
            self.mcp_client = MCPClient(in_memory_server=server)
        else:
            self.mcp_client = mcp_client

        self.mcp_client.connect()
        self.tool_registry = ToolRegistry()
        self._load_mcp_tools()

        self.react_agent = ReActAgent(
            llm_client=self.client,
            tool_registry=self.tool_registry,
            verbose=verbose,
        )

    def _load_mcp_tools(self) -> None:
        """Discover tools from MCP server and register them in agent registry."""
        mcp_tools = self.mcp_client.to_agent_tools()
        for t in mcp_tools:
            self.tool_registry._tools[t.name] = t
        self.logger.log("INIT", f"Loaded {len(mcp_tools)} tools from MCP server: {[t.name for t in mcp_tools]}")

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run the research agent with MCP tools."""
        return self.react_agent.run(user_query)
