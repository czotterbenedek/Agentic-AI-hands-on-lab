"""Lightweight ReAct agent loop implementation with tool execution and observability (Starter Lab)."""

import json
from typing import Any, Dict, List, Optional

from shared.agent import BaseAgent, Message, ToolCall
from shared.llm_client import BaseLLMClient, get_llm_client
from shared.logging import AgentLogger

try:
    from .tools import ToolRegistry, get_default_tool_registry
except ImportError:
    from tools import ToolRegistry, get_default_tool_registry

SYSTEM_PROMPT = """You are the University Research Assistant, an intelligent academic agent designed to assist graduate students and researchers.

You have access to tools to search academic papers, retrieve paper details, compute citation statistics, and perform mathematical calculations.

Follow the ReAct (Reasoning + Acting) protocol:
1. Thought: Reason about the user's request and what step to take next.
2. Action: Call the appropriate tool with structured arguments when external information or calculation is required.
3. Observation: Observe the output returned by the tool.
4. Final Answer: Once you have gathered sufficient information, synthesize a clear, helpful response.

Always cite paper IDs, titles, and publication years where applicable. If an expression or calculation is needed, rely on the calculate tool rather than mental math."""


class ReActAgent(BaseAgent):
    """ReAct Agent implementing an iterative Thought-Action-Observation loop."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_iterations: int = 5,
        verbose: bool = True,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        self.client = llm_client or get_llm_client()
        self.registry = tool_registry or get_default_tool_registry()
        self.max_iterations = max_iterations
        self.logger = AgentLogger(name="ResearchAgent", verbose=verbose)
        self.system_prompt = system_prompt
        self.messages: List[Message] = []
        self.step_count: int = 0

    def _execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a single tool call from the model with robust error handling.

        # ==============================================================================
        # TODO [Lab 1.4]: Safe Tool Execution & Error Handling (~45 lines)
        # ------------------------------------------------------------------------------
        # When an LLM outputs a tool call, we must safely look up and run the function:
        #
        # 1. Lookup the tool in `self.registry.get_tool(tool_call.name)`.
        #    If the tool is NOT found, log an error and return an informative error message
        #    listing the available registered tools. Do not crash!
        # 2. Parse arguments: `tool_call.arguments` might be a dict or a raw JSON string.
        #    If it's a string, deserialize it with `json.loads()`. Catch JSONDecodeError
        #    and return a clean error string if malformed.
        # 3. Log the action: call `self.logger.action(tool_call.name, args)`.
        # 4. Execute the tool: call `tool.execute(**args)` wrapped in a try/except block.
        # 5. Format the result:
        #    - If result is a dict or list, format with `json.dumps(..., indent=2)`.
        #    - Otherwise convert to string.
        # 6. Log the observation: call `self.logger.observation(...)`.
        # 7. Return the formatted result string.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 1.4]: Implement _execute_tool_call")

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run the ReAct agent on a user query until termination or max iterations.

        # ==============================================================================
        # TODO [Lab 1.5]: The Core ReAct Agent Loop (~85 lines)
        # ------------------------------------------------------------------------------
        # Implement the complete Thought -> Action -> Observation loop:
        #
        # 1. Initialize `self.messages` with:
        #    - A system message containing `self.system_prompt`
        #    - A user message containing `user_query`
        # 2. Reset `self.step_count = 0`.
        # 3. Retrieve available tool schemas from `self.registry.get_schemas()`.
        # 4. Enter a loop while `self.step_count < self.max_iterations`:
        #    a. Increment `self.step_count`.
        #    b. Call the LLM: `self.client.complete(messages=self.messages, tools=tool_schemas)`.
        #    c. Log the model's internal thought (if `response.content` is present)
        #       using `self.logger.thought(...)`.
        #    d. Check for Termination:
        #       If `response.tool_calls` is empty or None:
        #       - The agent has arrived at its final answer!
        #       - Log final answer: `self.logger.final_answer(...)`.
        #       - Append an assistant message to `self.messages`.
        #       - Return the final answer string.
        #    e. If `response.tool_calls` are present:
        #       - Append an assistant message to `self.messages` containing both
        #         `response.content` and `response.tool_calls`.
        #       - For each tool call in `response.tool_calls`:
        #         * Execute it with `self._execute_tool_call(tc)`
        #         * Append a Message with role="tool", tool_call_id=tc.id,
        #           name=tc.name, content=observation.
        # 5. If loop exits because `step_count >= max_iterations`:
        #    - Log error: agent reached maximum iterations.
        #    - Return an informative error message explaining that the limit was reached.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 1.5]: Implement ReAct run loop")
