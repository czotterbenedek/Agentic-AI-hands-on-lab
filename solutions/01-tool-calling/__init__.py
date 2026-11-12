"""Module 1: Tool Calling and ReAct Agent Loop."""

from .tools import (
    ToolRegistry,
    calculate,
    search_papers,
    get_paper_details,
    compute_citation_stats,
    summarize_paper,
    get_default_tool_registry,
)
from .react_agent import ReActAgent

__all__ = [
    "ToolRegistry",
    "calculate",
    "search_papers",
    "get_paper_details",
    "compute_citation_stats",
    "summarize_paper",
    "get_default_tool_registry",
    "ReActAgent",
]
