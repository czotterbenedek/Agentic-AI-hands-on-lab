"""Lightweight ReAct agent loop implementation with tool execution and observability."""

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
        """Execute a single tool call from the model with robust error handling."""
        tool = self.registry.get_tool(tool_call.name)
        if not tool:
            err = f"Error: Tool '{tool_call.name}' is not registered. Available tools: {[t.name for t in self.registry.list_tools()]}"
            self.logger.error(err)
            return err

        # Parse arguments
        args = tool_call.arguments
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception as e:
                err = f"Error: Failed to parse tool arguments JSON: {e}"
                self.logger.error(err)
                return err

        try:
            self.logger.action(tool_call.name, args)
            raw_result = tool.execute(**args)
            # Format result as JSON string or plain text
            if isinstance(raw_result, (dict, list)):
                result_str = json.dumps(raw_result, indent=2)
            else:
                result_str = str(raw_result)
            self.logger.observation(result_str)
            return result_str
        except Exception as e:
            err = f"Error executing tool '{tool_call.name}': {type(e).__name__}: {e}"
            self.logger.error(err)
            return err

    def run(self, user_query: str, **kwargs: Any) -> str:
        """Run the ReAct agent on a user query until termination or max iterations."""
        self.messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_query),
        ]
        self.step_count = 0
        tool_schemas = self.registry.get_schemas()

        while self.step_count < self.max_iterations:
            self.step_count += 1

            # Step 1: Call LLM with current conversation history and registered tool schemas
            response = self.client.complete(
                messages=self.messages,
                tools=tool_schemas,
            )

            # Step 2: Handle model reasoning / thought
            thought_text = response.content or ""
            if thought_text:
                self.logger.thought(thought_text)

            # Step 3: Check if the model decided to terminate without calling tools
            if not response.tool_calls:
                final_answer = thought_text or "Task completed."
                self.logger.final_answer(final_answer)
                self.messages.append(Message(role="assistant", content=final_answer))
                return final_answer

            # Step 4: Model requested one or more tool calls
            # First, append assistant response containing tool calls to context
            self.messages.append(
                Message(
                    role="assistant",
                    content=thought_text,
                    tool_calls=response.tool_calls,
                )
            )

            # Step 5: Execute each tool call and append observation message
            for tc in response.tool_calls:
                observation = self._execute_tool_call(tc)
                self.messages.append(
                    Message(
                        role="tool",
                        name=tc.name,
                        tool_call_id=tc.id,
                        content=observation,
                    )
                )

        # Loop exceeded maximum allowed iterations
        fallback_msg = (
            f"Agent reached maximum iterations ({self.max_iterations}) without reaching a final answer. "
            "Please refine your query or increase max_iterations."
        )
        self.logger.error(fallback_msg)
        return fallback_msg
