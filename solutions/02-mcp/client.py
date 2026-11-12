"""Model Context Protocol (MCP) Client connecting agents to MCP servers."""

import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

from shared.agent import Tool


class MCPClient:
    """Client for communicating with MCP servers via stdio or in-memory transport."""

    def __init__(self, server_path: Optional[str] = None, in_memory_server: Optional[Any] = None):
        self.server_path = server_path
        self.in_memory_server = in_memory_server
        self.process: Optional[subprocess.Popen] = None
        self._req_id: int = 0
        self.discovered_tools: Dict[str, Dict[str, Any]] = {}

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def connect(self) -> None:
        """Connect to MCP server and perform initialization handshake."""
        if self.in_memory_server is None and self.server_path:
            self.process = subprocess.Popen(
                [sys.executable, self.server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

        # Send initialize request
        init_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "ResearchAgentClient", "version": "1.0.0"},
                "capabilities": {},
            },
        }
        res = self._send_request(init_req)
        if "error" in res:
            raise ConnectionError(f"MCP Handshake failed: {res['error']}")

    def _send_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request to server and read response."""
        req_str = json.dumps(req)
        if self.in_memory_server is not None:
            res_str = self.in_memory_server.handle_request(req_str)
            return json.loads(res_str)

        if not self.process or not self.process.stdin or not self.process.stdout:
            raise ConnectionError("MCP server process is not running.")

        try:
            self.process.stdin.write(req_str + "\n")
            self.process.stdin.flush()
            line = self.process.stdout.readline()
            if not line:
                raise ConnectionError("MCP server closed connection unexpectedly.")
            return json.loads(line.strip())
        except Exception as e:
            raise ConnectionError(f"Error communicating with MCP server: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Query server for list of available tools via `tools/list`."""
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {},
        }
        res = self._send_request(req)
        if "error" in res:
            raise RuntimeError(f"Failed to list MCP tools: {res['error']}")

        tools_data = res.get("result", {}).get("tools", [])
        self.discovered_tools = {t["name"]: t for t in tools_data}
        return tools_data

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Call a remote tool on the MCP server via `tools/call`."""
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }
        res = self._send_request(req)
        if "error" in res:
            return f"MCP Error: {res['error'].get('message', 'Unknown error')}"

        result_data = res.get("result", {})
        content_items = result_data.get("content", [])
        if not content_items:
            return ""

        # Extract text from content items
        text_output = "\n".join(
            item.get("text", "") for item in content_items if item.get("type") == "text"
        )
        return text_output

    def to_agent_tools(self) -> List[Tool]:
        """Convert all discovered MCP tools into standard agent Tool instances."""
        if not self.discovered_tools:
            self.list_tools()

        tools: List[Tool] = []
        for name, info in self.discovered_tools.items():
            def make_executor(t_name: str):
                return lambda **kwargs: self.call_tool(t_name, kwargs)

            tools.append(
                Tool(
                    name=name,
                    description=info.get("description", ""),
                    parameters=info.get("inputSchema", {}),
                    func=make_executor(name),
                )
            )
        return tools

    def close(self) -> None:
        """Terminate the server process if running."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
            finally:
                self.process = None
