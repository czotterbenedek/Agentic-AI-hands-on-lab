"""Runnable demonstration for Module 2: Model Context Protocol (MCP) (Starter Lab)."""

import os
import sys

module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from client import MCPClient
from server import ResearchMCPServer
from mcp_agent import MCPAgent


def main() -> None:
    print("=" * 70)
    print("🎓 BME MSc AI in Practice - Lab 2: Model Context Protocol (MCP)")
    print("   Central Example: University Research Assistant with MCP Server (Starter Lab)")
    print("=" * 70)

    server = ResearchMCPServer()
    client = MCPClient(in_memory_server=server)

    try:
        client.connect()
        print("\n🔍 Step 1: Discovering MCP tools via protocol handshake...")
        tools = client.list_tools()
        print(f"Discovered {len(tools)} tools:")
        for t in tools:
            print(f"  • {t['name']}: {t['description']}")

        print("\n⚡ Step 2: Direct Tool Invocations via MCP JSON-RPC:")
        res1 = client.call_tool("search_papers", {"query": "transformer", "max_results": 2})
        print(f"search_papers ->\n{res1[:250]}...\n")

        res2 = client.call_tool("export_bibtex", {"paper_id": "1706.03762"})
        print(f"export_bibtex ->\n{res2}\n")

        print("\n🤖 Step 3: Running Agent with Dynamic MCP Tools:")
        agent = MCPAgent(mcp_client=client)
        answer = agent.run("Search research papers for transformer")
        print(f"\n[Agent Answer]:\n{answer}")

    except NotImplementedError as e:
        print(f"\n[TODO Required]: {e}")


if __name__ == "__main__":
    main()
