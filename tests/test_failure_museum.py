"""Regression tests for the 6 Failure Museum scenarios."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root and solution directories to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "solutions" / "01-tool-calling"))
sys.path.insert(0, str(ROOT_DIR / "solutions" / "02-mcp"))
sys.path.insert(0, str(ROOT_DIR / "solutions" / "03-memory"))
sys.path.insert(0, str(ROOT_DIR / "solutions" / "04-multi-agent"))

# Import solution components directly
import react_agent
import tools as sol_tools
import client as mcp_client_mod
import storage as sol_storage
import orchestrator as sol_orchestrator

ReActAgent = react_agent.ReActAgent
ToolRegistry = sol_tools.ToolRegistry
calculate = sol_tools.calculate
MCPClient = mcp_client_mod.MCPClient
SQLiteMemoryStorage = sol_storage.SQLiteMemoryStorage
MultiAgentOrchestrator = sol_orchestrator.MultiAgentOrchestrator

from shared.agent import AgentResponse, Tool, ToolCall
from shared.llm_client import BaseLLMClient, Message, MockLLMClient


# ------------------------------------------------------------------------------
# 1. Failure: Infinite ReAct Loop
# ------------------------------------------------------------------------------
class AlwaysToolCallingMockLLM(BaseLLMClient):
    """Mock LLM that never terminates, always requesting the search_papers tool."""

    def complete(self, messages, tools=None, temperature=0.0, max_tokens=1024):
        return AgentResponse(
            content="I need to keep searching forever.",
            tool_calls=[
                ToolCall(
                    id="call_infinite",
                    name="search_papers",
                    arguments={"query": "nonexistent topic"},
                )
            ],
        )


class TestFailure1InfiniteLoop(unittest.TestCase):
    def test_infinite_loop_guardrail_terminates_gracefully(self):
        """Verifies that an agent facing an infinite loop halts at max_iterations."""
        registry = ToolRegistry()
        registry.register(
            func=lambda query: "No results found.",
            name="search_papers",
            description="Search papers",
        )

        agent = ReActAgent(
            llm_client=AlwaysToolCallingMockLLM(),
            tool_registry=registry,
            max_iterations=3,
            verbose=False,
        )

        response = agent.run("Find this paper at all costs.")
        self.assertIn("maximum iterations (3)", response)
        self.assertEqual(agent.step_count, 3)


# ------------------------------------------------------------------------------
# 2. Failure: Hallucinated / Nonexistent Tool
# ------------------------------------------------------------------------------
class TestFailure2HallucinatedTool(unittest.TestCase):
    def test_hallucinated_tool_does_not_crash_agent(self):
        """Verifies that invoking an unregistered tool returns an error observation."""
        registry = ToolRegistry()
        agent = ReActAgent(
            llm_client=MockLLMClient(),
            tool_registry=registry,
            verbose=False,
        )

        hallucinated_call = ToolCall(
            id="call_fake",
            name="fetch_live_stock_price",
            arguments={"ticker": "AAPL"},
        )

        observation = agent._execute_tool_call(hallucinated_call)
        self.assertIn("Error: Tool 'fetch_live_stock_price' is not registered", observation)


# ------------------------------------------------------------------------------
# 3. Failure: Incorrect Tool Arguments
# ------------------------------------------------------------------------------
class TestFailure3IncorrectArguments(unittest.TestCase):
    def test_malformed_json_arguments_handled_gracefully(self):
        """Verifies that stringified invalid JSON arguments return an error observation."""
        registry = ToolRegistry()
        registry.register(
            func=lambda query: query,
            name="search_papers",
            description="Search papers",
        )
        agent = ReActAgent(
            llm_client=MockLLMClient(),
            tool_registry=registry,
            verbose=False,
        )

        invalid_json_call = ToolCall(
            id="call_bad_json",
            name="search_papers",
            arguments='{"query": unquoted_value}',  # Invalid JSON syntax
        )

        observation = agent._execute_tool_call(invalid_json_call)
        self.assertIn("Error: Failed to parse tool arguments JSON", observation)

    def test_safe_calculator_handles_division_by_zero(self):
        """Verifies calculator catches zero-division without raising uncaught exception."""
        result = calculate("10 / 0")
        self.assertEqual(result, "Error: Division by zero")

    def test_safe_calculator_rejects_unsafe_expressions(self):
        """Verifies calculator rejects arbitrary code execution attempts."""
        result = calculate("__import__('os').system('echo pwned')")
        self.assertIn("Error", result)


# ------------------------------------------------------------------------------
# 4. Failure: MCP Server Connection Failure
# ------------------------------------------------------------------------------
class TestFailure4MCPConnectionFailure(unittest.TestCase):
    def test_mcp_client_raises_connection_error_on_invalid_server(self):
        """Verifies client raises ConnectionError when server script does not exist."""
        client = MCPClient(server_path="/path/to/nonexistent/mcp_server.py")
        with self.assertRaises(ConnectionError):
            client.connect()

    def test_mcp_client_detects_dead_process_on_send(self):
        """Verifies client raises ConnectionError when attempting to write to unstarted process."""
        client = MCPClient(server_path=None, in_memory_server=None)
        with self.assertRaises(ConnectionError) as ctx:
            client.call_tool("search_papers", {"query": "test"})
        self.assertIn("MCP server process is not running", str(ctx.exception))


# ------------------------------------------------------------------------------
# 5. Failure: Contaminated Memory / Cross-User Leakage
# ------------------------------------------------------------------------------
class TestFailure5MemoryContamination(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.storage = SQLiteMemoryStorage(db_path=self.temp_db.name)

    def tearDown(self):
        try:
            os.remove(self.temp_db.name)
        except OSError:
            pass

    def test_strict_user_isolation_prevents_preference_leakage(self):
        """Verifies Alice's preferences are completely isolated and invisible to Bob."""
        self.storage.save_preference("alice", "preferred_topic", "Quantum Computing")
        self.storage.save_preference("alice", "citation_style", "IEEE")

        # Bob queries his preferences
        bob_prefs = self.storage.get_preferences("bob")
        self.assertEqual(bob_prefs, {}, "Bob should not see any of Alice's preferences!")

        # Alice queries her preferences
        alice_prefs = self.storage.get_preferences("alice")
        self.assertEqual(alice_prefs.get("preferred_topic"), "Quantum Computing")


# ------------------------------------------------------------------------------
# 6. Failure: Multi-Agent Delegation Loop
# ------------------------------------------------------------------------------
class TestFailure6MultiAgentDelegationLoop(unittest.TestCase):
    def test_cycle_detection_stops_ping_pong_delegation(self):
        """Verifies detect_cycle halts cyclical A -> B -> A -> B delegation."""
        orchestrator = MultiAgentOrchestrator()

        # Simulate 2-cycle alternating between researcher and analyst
        cyclical_history = [
            {"source": "analyst", "target": "researcher"},
            {"source": "researcher", "target": "analyst"},
            {"source": "analyst", "target": "researcher"},
            {"source": "researcher", "target": "analyst"},
        ]

        has_cycle = orchestrator.detect_cycle(cyclical_history)
        self.assertTrue(has_cycle, "detect_cycle must identify alternating 2-cycles!")

    def test_acyclic_delegation_is_permitted(self):
        """Verifies standard linear delegation history is not falsely flagged as a cycle."""
        orchestrator = MultiAgentOrchestrator()

        linear_history = [
            {"source": "supervisor", "target": "researcher"},
            {"source": "supervisor", "target": "analyst"},
        ]

        has_cycle = orchestrator.detect_cycle(linear_history)
        self.assertFalse(has_cycle, "Linear delegation should not be flagged as a cycle.")


if __name__ == "__main__":
    unittest.main()
