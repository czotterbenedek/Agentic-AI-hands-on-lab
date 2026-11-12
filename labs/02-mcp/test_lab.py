"""Unit and integration tests for Module 2: Model Context Protocol (MCP)."""

import json
import os
import sys

try:
    import pytest
except ImportError:
    pytest = None

module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from server import ResearchMCPServer
from client import MCPClient
from mcp_agent import MCPAgent


def test_mcp_server_initialize():
    """Verify MCP protocol initialization handshake."""
    server = ResearchMCPServer()
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    res = json.loads(server.handle_request(req))
    assert res["id"] == 1
    assert "serverInfo" in res["result"]
    assert res["result"]["serverInfo"]["name"] == "research-server"


def test_mcp_server_tools_list():
    """Verify listing tools via MCP tools/list method."""
    server = ResearchMCPServer()
    req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    res = json.loads(server.handle_request(req))
    tools = res["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "search_papers" in tool_names
    assert "get_paper_details" in tool_names
    assert "get_recent_papers" in tool_names
    assert "export_bibtex" in tool_names
    assert "get_author_papers" in tool_names


def test_mcp_server_search_tool():
    """Verify executing search_papers via tools/call."""
    server = ResearchMCPServer()
    req = json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "search_papers", "arguments": {"query": "transformer", "max_results": 2}},
    })
    res = json.loads(server.handle_request(req))
    assert not res["result"].get("isError", False)
    content = json.loads(res["result"]["content"][0]["text"])
    assert len(content) > 0
    assert "Attention" in content[0]["title"]


def test_mcp_server_bibtex_tool():
    """Verify export_bibtex student exercise tool."""
    server = ResearchMCPServer()
    req = json.dumps({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "export_bibtex", "arguments": {"paper_id": "1706.03762"}},
    })
    res = json.loads(server.handle_request(req))
    text = res["result"]["content"][0]["text"]
    assert "@article" in text
    assert "Attention is all you need" in text.lower() or "vaswani" in text.lower()


def test_mcp_client_integration():
    """Verify MCPClient connects, lists tools, and executes calls."""
    server = ResearchMCPServer()
    client = MCPClient(in_memory_server=server)
    client.connect()
    tools = client.list_tools()
    assert len(tools) >= 5
    out = client.call_tool("get_paper_details", {"paper_id": "2106.09685"})
    assert "LoRA" in out


def test_mcp_agent_run():
    """Verify MCPAgent end-to-end execution."""
    agent = MCPAgent(verbose=False)
    answer = agent.run("Find papers about lora")
    assert "LoRA" in answer or "tool results" in answer


if __name__ == "__main__":
    tests = [
        test_mcp_server_initialize,
        test_mcp_server_tools_list,
        test_mcp_server_search_tool,
        test_mcp_server_bibtex_tool,
        test_mcp_client_integration,
        test_mcp_agent_run,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✓ {t.__name__} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__} FAILED: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
    if passed != len(tests):
        sys.exit(1)
