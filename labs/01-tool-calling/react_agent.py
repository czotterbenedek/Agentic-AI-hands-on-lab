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

        Basic implementation provided: tool lookup and argument JSON deserialization.
        """
        # 1. Lookup the tool in registry
        tool = self.registry.get_tool(tool_call.name)
        if not tool:
            err = f"Error: Tool '{tool_call.name}' is not registered. Available tools: {[t.name for t in self.registry.list_tools()]}"
            self.logger.error(err)
            return err

        # 2. Parse arguments (handles dictionary or raw JSON string from LLM)
        args = tool_call.arguments
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception as e:
                err = f"Error: Failed to parse tool arguments JSON: {e}"
                self.logger.error(err)
                return err

        # ==============================================================================
        # TODO [Lab 1.3]: Execute Tool and Format Observation (~15 lines)
        # ------------------------------------------------------------------------------
        # Extend the execution part:
        # 1. Log the action: call `self.logger.action(tool_call.name, args)`.
        # 2. Execute the tool: call `raw_result = tool.execute(**args)` wrapped in try/except.
        # 3. Format the result string:
        #    - If result is a dict or list, format with `json.dumps(raw_result, indent=2)`.
        #    - Otherwise convert to `str(raw_result)`.
        # 4. Log the observation: call `self.logger.observation(result_str)`.
        # 5. Return `result_str`. Catch any Exception and return error string:
        #    f"Error executing tool: {e}".
        # ==============================================================================
        raise NotImplementedError("TODO [Lab 1.3]: Implement tool execution and observation logging")

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run the ReAct agent on a user query until termination or max iterations.

        Basic implementation provided: message initialization, schema retrieval,
        while loop skeleton, thought logging, final answer termination, and iteration limit.
        """
        # 1. Initialize context with system prompt and user inquiry
        self.messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_query),
        ]
        self.step_count = 0
        tool_schemas = self.registry.get_schemas()

        while self.step_count < self.max_iterations:
            self.step_count += 1

            # Step 1: Model completion request
            response = self.client.complete(
                messages=self.messages,
                tools=tool_schemas,
            )

            # Step 2: Handle model reasoning / thought
            thought_text = response.content or ""
            if thought_text:
                self.logger.thought(thought_text)

            # Step 3: Check for termination (no tool calls requested)
            if not response.tool_calls:
                final_answer = thought_text or "Task completed."
                self.logger.final_answer(final_answer)
                self.messages.append(Message(role="assistant", content=final_answer))
                return final_answer

            # Step 4: Model requested one or more tool calls
            # ==============================================================================
            # TODO [Lab 1.4]: Handle Tool Calls and Record Observations in ReAct Loop (~15 lines)
            # ------------------------------------------------------------------------------
            # When the LLM decides to take an action:
            # 1. Append the assistant message with `thought_text` and `response.tool_calls`
            #    to `self.messages`:
            #    `self.messages.append(Message(role="assistant", content=thought_text, tool_calls=response.tool_calls))`
            # 2. For each tool call `tc` in `response.tool_calls`:
            #    a. Execute it: `observation = self._execute_tool_call(tc)`
            #    b. Append a tool observation message to `self.messages`:
            #       `self.messages.append(Message(role="tool", name=tc.name, tool_call_id=tc.id, content=observation))`
            # ==============================================================================
            raise NotImplementedError("TODO [Lab 1.4]: Handle tool calls and observations in ReAct loop")

        # 5. Iteration limit reached
        fallback_msg = (
            f"Agent reached maximum iterations ({self.max_iterations}) without reaching a final answer. "
            "Please refine your query or increase max_iterations."
        )
        self.logger.error(fallback_msg)
        return fallback_msg
