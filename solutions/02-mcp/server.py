"""Standalone Model Context Protocol (MCP) Server for Research Tools."""

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
        """Search research papers using public bibliographic dataset with Crossref fallback."""
        if not query or not query.strip():
            return json.dumps({"error": "Query cannot be empty"})

        count = limit if limit is not None else max_results

        # Try live Crossref first, fallback to local curated dataset
        crossref_res = search_crossref_api(query, limit=count)
        if crossref_res:
            return json.dumps(crossref_res, indent=2)

        # Fallback to local dataset
        q_lower = query.lower()
        matches = []
        for paper in RESEARCH_DATASET:
            score = 0
            if q_lower in paper["title"].lower():
                score += 3
            if any(q_lower in t.lower() for t in paper.get("topics", [])):
                score += 2
            if q_lower in paper["abstract"].lower():
                score += 1

            if score > 0:
                matches.append(paper)

        matches.sort(key=lambda p: p["citations"], reverse=True)
        return json.dumps(matches[:count], indent=2)

    def get_paper_details(self, paper_id: str) -> str:
        """Retrieve complete bibliographic details for a paper by ID or DOI."""
        pid = str(paper_id).strip()
        for paper in RESEARCH_DATASET:
            if paper["paper_id"] == pid or paper.get("doi") == pid:
                return json.dumps(paper, indent=2)
        return json.dumps({"error": f"Paper '{paper_id}' not found in database"})

    def get_recent_papers(self, topic: str, limit: int = 5) -> str:
        """Retrieve the most recent papers for a given academic topic."""
        t_lower = topic.lower().strip()
        matching = [
            p for p in RESEARCH_DATASET
            if t_lower in p["title"].lower() or any(t_lower in t.lower() for t in p.get("topics", []))
        ]
        # Sort descending by year, then by citations
        matching.sort(key=lambda p: (p["year"], p["citations"]), reverse=True)
        return json.dumps(matching[:limit], indent=2)

    # --------------------------------------------------------------------------
    # Student Exercise MCP Tools
    # --------------------------------------------------------------------------

    def export_bibtex(self, paper_id: str) -> str:
        """Export BibTeX citation entry for a given paper ID."""
        pid = str(paper_id).strip()
        for paper in RESEARCH_DATASET:
            if paper["paper_id"] == pid or paper.get("doi") == pid:
                bib = paper.get("bibtex")
                if bib:
                    return bib
                # Construct synthetic BibTeX
                authors_str = " and ".join(paper["authors"])
                first_author = paper["authors"][0].split()[-1].lower() if paper["authors"] else "author"
                year = paper["year"]
                return (
                    f"@article{{{first_author}{year},\n"
                    f"  title={{{paper['title']}}},\n"
                    f"  author={{{authors_str}}},\n"
                    f"  year={{{year}}}\n"
                    f"}}"
                )
        return f"% Error: Paper '{paper_id}' not found."

    def get_author_papers(self, author_name: str) -> str:
        """Retrieve all papers authored or co-authored by a specific researcher."""
        author_lower = author_name.lower().strip()
        results = []
        for paper in RESEARCH_DATASET:
            if any(author_lower in a.lower() for a in paper.get("authors", [])):
                results.append({
                    "paper_id": paper["paper_id"],
                    "title": paper["title"],
                    "year": paper["year"],
                    "citations": paper["citations"],
                })
        results.sort(key=lambda p: p["year"], reverse=True)
        return json.dumps(results, indent=2)

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
        """Handle incoming JSON-RPC 2.0 request and return JSON response."""
        try:
            req = json.loads(request_str)
        except Exception as e:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            })

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": self.name, "version": self.version},
                    "capabilities": {"tools": {}},
                },
            })

        elif method == "ping":
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}})

        elif method == "tools/list":
            tools_list = [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["inputSchema"],
                }
                for t in self.tools.values()
            ]
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}})

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if tool_name not in self.tools:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method/Tool '{tool_name}' not found"},
                })

            handler = self.tools[tool_name]["handler"]
            try:
                res = handler(**tool_args)
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": str(res)}],
                        "isError": False,
                    },
                })
            except Exception as e:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {e}"}],
                        "isError": True,
                    },
                })

        return json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unsupported method '{method}'"},
        })

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
