"""Model Context Protocol (MCP) Client connecting agents to MCP servers (Starter Lab)."""

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
        """Connect to MCP server and perform initialization handshake.

        # ==============================================================================
        # TODO [Lab 2.4a]: MCP Client Connection & Handshake (~25 lines)
        # ------------------------------------------------------------------------------
        # 1. If `self.in_memory_server` is None and `self.server_path` is given:
        #    Spawn server process using `subprocess.Popen` with stdin/stdout piped.
        # 2. Build JSON-RPC request for method="initialize" with protocolVersion and clientInfo.
        # 3. Send request via `self._send_request(init_req)`.
        # 4. Check for error in response; raise ConnectionError if handshake fails.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.4a]: Implement connect handshake")

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
        """Query server for list of available tools via `tools/list`.

        # ==============================================================================
        # TODO [Lab 2.4b]: Tool Discovery via MCP Protocol (~20 lines)
        # ------------------------------------------------------------------------------
        # 1. Send JSON-RPC request with method="tools/list" and empty params.
        # 2. If response has "error", raise RuntimeError.
        # 3. Extract tools array from `result.tools`.
        # 4. Store in `self.discovered_tools` keyed by tool name.
        # 5. Return the list of tool definitions.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.4b]: Implement list_tools")

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """Call a remote tool on the MCP server via `tools/call`.

        # ==============================================================================
        # TODO [Lab 2.5]: Remote MCP Tool Execution (~40 lines)
        # ------------------------------------------------------------------------------
        # 1. Construct JSON-RPC request for method="tools/call" with params {"name": ..., "arguments": ...}.
        # 2. Send request to server using `self._send_request(...)`.
        # 3. If response has "error", return error message string.
        # 4. Parse `result.content` array of content items.
        # 5. Extract text from items where type == "text" and join with newlines.
        # 6. Return the resulting output string.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 2.5]: Implement call_tool")

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
