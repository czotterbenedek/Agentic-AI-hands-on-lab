"""Standalone Model Context Protocol (MCP) Server for Research Tools (Starter Lab)."""

import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional

try:
    from .dataset import RESEARCH_DATASET, search_crossref_api
except ImportError:
    from dataset import RESEARCH_DATASET, search_crossref_api


class ResearchMCPServer:
    """MCP Server exposing academic research tools over JSON-RPC 2.0 stdio."""

    def __init__(self, name: str = "research-server", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        """Register an MCP tool with schema and execution handler."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": parameters,
            "handler": handler,
        }

    # --------------------------------------------------------------------------
    # Core MCP Tool Implementations
    # --------------------------------------------------------------------------

    def search_papers(self, query: str, max_results: int = 5, limit: Optional[int] = None, **kwargs: Any) -> str:
        """Search research papers using public bibliographic dataset with Crossref fallback.

        # ==============================================================================
        # TODO [Lab 2.2a]: Implement MCP search_papers tool (~20 lines)
        # ------------------------------------------------------------------------------
        # 1. Validate query is non-empty. If empty, return JSON {"error": "..."}.
        # 2. Determine count: `limit if limit is not None else max_results`.
        # 3. Call `search_crossref_api(query, limit=count)`. If non-null, return `json.dumps(..., indent=2)`.
        # 4. Fallback: filter `RESEARCH_DATASET` matching title, topics, or abstract against query.
        #    Sort matching papers descending by citations.
        # 5. Return JSON serialized string of top results.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.2a]: Implement search_papers tool")

    def get_paper_details(self, paper_id: str) -> str:
        """Retrieve complete bibliographic details for a paper by ID or DOI.

        # ==============================================================================
        # TODO [Lab 2.2b]: Implement MCP get_paper_details tool (~15 lines)
        # ------------------------------------------------------------------------------
        # 1. Search `RESEARCH_DATASET` for a paper matching `paper_id` or `doi`.
        # 2. If found, return its JSON representation formatted with indent=2.
        # 3. If not found, return JSON with {"error": "Paper '...' not found in database"}.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.2b]: Implement get_paper_details tool")

    def get_recent_papers(self, topic: str, limit: int = 5) -> str:
        """Retrieve the most recent papers for a given academic topic.

        # ==============================================================================
        # TODO [Lab 2.2c]: Implement MCP get_recent_papers tool (~15 lines)
        # ------------------------------------------------------------------------------
        # 1. Filter `RESEARCH_DATASET` for papers matching topic in title or topics list.
        # 2. Sort results descending by publication year, then by citations.
        # 3. Return JSON formatted string of the top `limit` papers.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.2c]: Implement get_recent_papers tool")

    # --------------------------------------------------------------------------
    # Student Exercise MCP Tools
    # --------------------------------------------------------------------------

    def export_bibtex(self, paper_id: str) -> str:
        """Export BibTeX citation entry for a given paper ID.

        # ==============================================================================
        # TODO [Lab 2.3a]: Student Exercise - Implement export_bibtex tool (~20 lines)
        # ------------------------------------------------------------------------------
        # 1. Locate paper in `RESEARCH_DATASET` by `paper_id`.
        # 2. If the paper has a 'bibtex' field, return it directly.
        # 3. Otherwise generate synthetic BibTeX entry:
        #    @article{<key>, title={...}, author={...}, year={...}}
        # 4. If not found, return an error message "% Error: Paper not found."
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.3a]: Implement export_bibtex tool")

    def get_author_papers(self, author_name: str) -> str:
        """Retrieve all papers authored or co-authored by a specific researcher.

        # ==============================================================================
        # TODO [Lab 2.3b]: Student Exercise - Implement get_author_papers tool (~20 lines)
        # ------------------------------------------------------------------------------
        # 1. Case-insensitively match `author_name` against authors in `RESEARCH_DATASET`.
        # 2. Extract paper_id, title, year, citations.
        # 3. Sort descending by publication year.
        # 4. Return as JSON string.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.3b]: Implement get_author_papers tool")

    def _register_default_tools(self) -> None:
        """Register the default research tools with their JSON schemas."""
        self.register_tool(
            name="search_papers",
            description="Search academic research papers by query keywords or topic.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords, e.g. 'transformer'"},
                    "max_results": {"type": "integer", "description": "Max results to return", "default": 5},
                },
                "required": ["query"],
            },
            handler=self.search_papers,
        )
        self.register_tool(
            name="get_paper_details",
            description="Get full metadata, abstract, and citation details for a paper by ID.",
            parameters={
                "type": "object",
                "properties": {
                    "paper_id": {"type": "string", "description": "Paper ID or DOI, e.g. '1706.03762'"},
                },
                "required": ["paper_id"],
            },
            handler=self.get_paper_details,
        )
        self.register_tool(
            name="get_recent_papers",
            description="Retrieve recent papers on a specific topic, ordered by publication year.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic or field name, e.g. 'agent'"},
                    "limit": {"type": "integer", "description": "Maximum number of papers", "default": 5},
                },
                "required": ["topic"],
            },
            handler=self.get_recent_papers,
        )
        self.register_tool(
            name="export_bibtex",
            description="Export standard BibTeX citation entry for a research paper.",
            parameters={
                "type": "object",
                "properties": {
                    "paper_id": {"type": "string", "description": "Paper ID to export BibTeX for"},
                },
                "required": ["paper_id"],
            },
            handler=self.export_bibtex,
        )
        self.register_tool(
            name="get_author_papers",
            description="Retrieve all research papers authored by a specific researcher.",
            parameters={
                "type": "object",
                "properties": {
                    "author_name": {"type": "string", "description": "Name of author, e.g. 'Vaswani'"},
                },
                "required": ["author_name"],
            },
            handler=self.get_author_papers,
        )

    # --------------------------------------------------------------------------
    # JSON-RPC 2.0 Protocol Dispatcher
    # --------------------------------------------------------------------------

    def handle_request(self, request_str: str) -> str:
        """Handle incoming JSON-RPC 2.0 request and return JSON response.

        # ==============================================================================
        # TODO [Lab 2.1]: JSON-RPC 2.0 Protocol Dispatcher (~65 lines)
        # ------------------------------------------------------------------------------
        # The Model Context Protocol uses JSON-RPC 2.0 messages over standard I/O:
        #
        # 1. Parse `request_str` with `json.loads()`. If invalid JSON, return standard
        #    JSON-RPC parse error (-32700).
        # 2. Extract `id`, `method`, and `params`.
        # 3. Handle method == "initialize":
        #    - Return protocolVersion ("2024-11-05"), serverInfo ({name, version}),
        #      and capabilities ({"tools": {}}).
        # 4. Handle method == "ping":
        #    - Return empty result: {"jsonrpc": "2.0", "id": req_id, "result": {}}.
        # 5. Handle method == "tools/list":
        #    - Return list of registered tools with name, description, and inputSchema.
        # 6. Handle method == "tools/call":
        #    - Extract tool name and arguments from params.
        #    - If tool not registered, return method not found error (-32601).
        #    - Execute handler with arguments, format result as:
        #      {"content": [{"type": "text", "text": str(res)}], "isError": False}
        #    - Catch any exceptions and set "isError": True.
        # 7. For unknown methods, return JSON-RPC error code -32601.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.1]: Implement handle_request dispatcher")

    def run_stdio(self) -> None:
        """Run server listening for JSON-RPC messages on stdin and writing to stdout."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            response = self.handle_request(line)
            sys.stdout.write(response + "\n")
            sys.stdout.flush()


def main() -> None:
    server = ResearchMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
