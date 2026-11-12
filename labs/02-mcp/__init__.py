"""Module 2: Model Context Protocol (MCP) Server and Client (Starter Lab)."""

from .dataset import RESEARCH_DATASET
from .server import ResearchMCPServer
from .client import MCPClient
from .mcp_agent import MCPAgent

__all__ = [
    "RESEARCH_DATASET",
    "ResearchMCPServer",
    "MCPClient",
    "MCPAgent",
]
