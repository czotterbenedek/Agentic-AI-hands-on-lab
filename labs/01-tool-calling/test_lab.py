"""Unit and integration tests for Module 1: Tool Calling and ReAct Agent."""

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

from tools import (
    ToolRegistry,
    calculate,
    search_papers,
    get_paper_details,
    compute_citation_stats,
    summarize_paper,
    get_default_tool_registry,
    generate_json_schema,
)
from react_agent import ReActAgent
from shared.llm_client import MockLLMClient
from shared.agent import ToolCall, AgentResponse


def test_generate_json_schema():
    """Verify that JSON schema generator properly extracts types and docstrings."""
    schema = generate_json_schema(calculate)
    assert schema["type"] == "object"
    assert "expression" in schema["properties"]
    assert schema["properties"]["expression"]["type"] == "string"
    assert "expression" in schema["required"]


def test_tool_registry():
    """Verify registration and lookup of tools."""
    registry = ToolRegistry()
    registry.register(calculate)
    tool = registry.get_tool("calculate")
    assert tool is not None
    assert tool.name == "calculate"
    assert len(registry.get_schemas()) == 1


def test_calculate_tool_safety():
    """Verify math evaluation and security blocking of unsafe code."""
    assert calculate("2 + 2 * 10") == "22"
    assert calculate("100 / 4") == "25.0"
    # Unsafe code injection attempt must fail
    res = calculate("__import__('os').system('ls')")
    assert "Error" in res or "forbidden" in res


def test_search_papers():
    """Verify paper search by keyword."""
    results = search_papers("transformer", limit=3)
    assert len(results) > 0
    assert any("Attention" in p["title"] or "BERT" in p["title"] for p in results)


def test_compute_citation_stats():
    """Verify citation calculation across multiple papers."""
    stats = compute_citation_stats(["1706.03762", "2106.09685"])
    assert stats["paper_count"] == 2
    assert stats["total_citations"] == 125000 + 18500
    assert abs(stats["average_citations"] - (125000 + 18500) / 2) < 0.01


def test_react_agent_single_step():
    """Verify agent execution with calculation query."""
    agent = ReActAgent(llm_client=MockLLMClient(), verbose=False)
    answer = agent.run("Calculate 25 * 4")
    assert "100" in answer or "tool results" in answer


def test_react_agent_max_iterations():
    """Verify infinite loop protection when model never produces a final answer."""
    class LoopingLLMClient(MockLLMClient):
        def complete(self, messages, tools=None, temperature=0.0):
            return AgentResponse(
                content="I will call calculate again.",
                tool_calls=[ToolCall(id="loop", name="calculate", arguments={"expression": "1+1"})],
            )

    agent = ReActAgent(llm_client=LoopingLLMClient(), max_iterations=3, verbose=False)
    answer = agent.run("Do something infinite")
    assert "maximum iterations" in answer.lower()


def test_react_agent_invalid_tool_recovery():
    """Verify agent handles hallucinated/unregistered tool gracefully."""
    class HallucinatingLLMClient(MockLLMClient):
        def __init__(self):
            super().__init__()
            self.step = 0

        def complete(self, messages, tools=None, temperature=0.0):
            self.step += 1
            if self.step == 1:
                return AgentResponse(
                    content="Calling nonexistent tool",
                    tool_calls=[ToolCall(id="call_1", name="nonexistent_magic_tool", arguments={})],
                )
            return AgentResponse(
                content="Recovered after tool error",
                tool_calls=[],
                finish_reason="stop",
            )

    agent = ReActAgent(llm_client=HallucinatingLLMClient(), verbose=False)
    answer = agent.run("Test invalid tool")
    assert "Recovered" in answer


if __name__ == "__main__":
    tests = [
        test_generate_json_schema,
        test_tool_registry,
        test_calculate_tool_safety,
        test_search_papers,
        test_compute_citation_stats,
        test_react_agent_single_step,
        test_react_agent_max_iterations,
        test_react_agent_invalid_tool_recovery,
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
