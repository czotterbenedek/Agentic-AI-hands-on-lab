"""LLM Client implementations: Base interface, OpenAI/Ollama client, and MockLLMClient."""

import json
import re
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from shared.agent import AgentResponse, Message, ToolCall
from shared.config import Settings, get_settings

try:
    from openai import OpenAI
    HAS_OPENAI_SDK = True
except ImportError:
    OpenAI = None
    HAS_OPENAI_SDK = False


class BaseLLMClient(ABC):
    """Abstract interface for LLM completion and tool calling."""

    @abstractmethod
    def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> AgentResponse:
        """Generate a completion for the given messages and optional tools."""
        pass


class OpenAILLMClient(BaseLLMClient):
    """Client using the official OpenAI Python SDK (compatible with OpenAI, Ollama, VLLM)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key or "sk-no-key-required"
        self.base_url = (
            base_url
            or (settings.ollama_base_url if settings.llm_provider == "ollama" else "https://api.openai.com/v1")
        ).rstrip("/")
        self.model = model or settings.llm_model

        self.sdk_client = None
        if HAS_OPENAI_SDK:
            try:
                self.sdk_client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception:
                self.sdk_client = None

    def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> AgentResponse:
        """Send completion request using the official OpenAI Python SDK or fallback REST."""
        if self.sdk_client is not None:
            return self._complete_with_sdk(messages, tools, temperature)
        return self._complete_with_rest(messages, tools, temperature)

    def _complete_with_sdk(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> AgentResponse:
        """Complete using the official openai.OpenAI SDK client."""
        payload_messages = [m.to_dict() for m in messages]
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = self.sdk_client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            msg = choice.message

            tool_calls: List[ToolCall] = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    args_raw = tc.function.arguments
                    try:
                        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                    except Exception:
                        args = {"raw": args_raw}
                    tool_calls.append(ToolCall(id=tc.id, name=fn_name, arguments=args))

            return AgentResponse(
                content=msg.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                raw=response.model_dump() if hasattr(response, "model_dump") else {},
            )
        except Exception as e:
            # If SDK call fails, attempt fallback to direct REST
            return self._complete_with_rest(messages, tools, temperature)

    def _complete_with_rest(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> AgentResponse:
        """Fallback completion using standard library HTTP REST request."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"LLM API Error ({e.code}): {e.reason} - {err_body}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to LLM endpoint at {url}: {e}")

        choice = data["choices"][0]
        msg = choice.get("message", {})
        tool_calls_data = msg.get("tool_calls", [])

        tool_calls: List[ToolCall] = []
        for tc in tool_calls_data:
            func = tc.get("function", {})
            name = func.get("name", "")
            args_raw = func.get("arguments", "{}")
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except Exception:
                args = {"raw": args_raw}
            tool_calls.append(ToolCall(id=tc.get("id", f"call_{name}"), name=name, arguments=args))

        return AgentResponse(
            content=msg.get("content"),
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason"),
            raw=data,
        )


class MockLLMClient(BaseLLMClient):
    """Deterministic Mock LLM Client for testing, offline labs, and predictable evaluation.

    Simulates realistic Research Assistant reasoning, tool calling, and answer generation
    without requiring API keys or network access.
    """

    def __init__(self, model_name: str = "mock-gpt-4o"):
        self.model_name = model_name
        self.call_count = 0

    def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> AgentResponse:
        self.call_count += 1
        available_tools = {}
        if tools:
            for t in tools:
                name = t.get("function", {}).get("name")
                if name:
                    available_tools[name] = t.get("function", {})

        # Check last message
        last_message = messages[-1] if messages else Message(role="user", content="")

        # 1. If last message is a TOOL observation, synthesize final answer or next action
        if last_message.role == "tool":
            tool_name = last_message.name or ""
            obs_content = last_message.content or ""

            # Check if there are other questions pending in history
            user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")

            # If tool was paper search and user also asked to calculate or summarize
            if "search" in tool_name.lower() and ("calculate" in user_msg.lower() or "average" in user_msg.lower()) and "calculate" in available_tools:
                # Find citations in observation
                citations = re.findall(r'"citation_count":\s*(\d+)', obs_content)
                if not citations:
                    citations = re.findall(r'"citations":\s*(\d+)', obs_content)
                if citations:
                    expr = " + ".join(citations[:3])
                    return AgentResponse(
                        content=f"Now calculating total/average citations from retrieved papers: {expr}",
                        tool_calls=[
                            ToolCall(
                                id=f"mock_call_{self.call_count}",
                                name="calculate",
                                arguments={"expression": f"({expr}) / {len(citations[:3])}"},
                            )
                        ],
                    )

            # Final synthesis after tool execution
            return AgentResponse(
                content=(
                    f"Based on the tool results for {tool_name}:\n{obs_content[:300]}...\n"
                    "I have synthesized the findings for your academic research inquiry."
                ),
                tool_calls=[],
                finish_reason="stop",
            )

        # 2. First turn / user query - determine tool call based on query keywords
        user_content = last_message.content or ""
        query = user_content.lower()

        # Paper search query
        if ("paper" in query or "attention" in query or "bert" in query or "lora" in query or "agent" in query or "transformer" in query or "prompting" in query) and "search_papers" in available_tools:
            # Extract topic
            topic = "transformer"
            for t in ["attention", "bert", "lora", "react", "chain-of-thought", "prompting", "transformer"]:
                if t in query:
                    topic = t
                    break
            return AgentResponse(
                content=f"I need to search the academic database for research papers on '{topic}'.",
                tool_calls=[
                    ToolCall(
                        id=f"mock_call_{self.call_count}",
                        name="search_papers",
                        arguments={"query": topic, "limit": 3},
                    )
                ],
            )

        # Calculation query
        if ("calculate" in query or "math" in query or re.search(r'\d+\s*[\+\-\*\/]\s*\d+', query)) and "calculate" in available_tools:
            match = re.search(r'(\d+[\d\.\s\+\-\*\/\(\)]*\d+)', user_content)
            expr = match.group(1).strip() if match else "2 + 2"
            return AgentResponse(
                content="I need to calculate this arithmetic expression.",
                tool_calls=[
                    ToolCall(
                        id=f"mock_call_{self.call_count}",
                        name="calculate",
                        arguments={"expression": expr},
                    )
                ],
            )

        # Paper details
        if "details" in query and "get_paper_details" in available_tools:
            match = re.search(r'paper[-_\s]?(\d+|[a-zA-Z0-9\.\-]+)', query)
            pid = match.group(1) if match else "1706.03762"
            return AgentResponse(
                content="Retrieving details for the requested paper.",
                tool_calls=[
                    ToolCall(
                        id=f"mock_call_{self.call_count}",
                        name="get_paper_details",
                        arguments={"paper_id": pid},
                    )
                ],
            )

        # Memory save / recall
        if ("remember" in query or "preference" in query or "save interest" in query) and "save_preference" in available_tools:
            return AgentResponse(
                content="Saving your research preference.",
                tool_calls=[
                    ToolCall(
                        id=f"mock_call_{self.call_count}",
                        name="save_preference",
                        arguments={"key": "research_topic", "value": user_content},
                    )
                ],
            )

        # Multi-agent handoff delegation
        if "delegate" in query or "handoff" in query or "analyze" in query:
            if "handoff_to_specialist" in available_tools:
                return AgentResponse(
                    content="Delegating task to specialist.",
                    tool_calls=[
                        ToolCall(
                            id=f"mock_call_{self.call_count}",
                            name="handoff_to_specialist",
                            arguments={"agent_role": "researcher", "task": user_content},
                        )
                    ],
                )

        # Fallback direct response
        return AgentResponse(
            content=f"University Research Assistant Response: {user_content}",
            tool_calls=[],
            finish_reason="stop",
        )


def get_llm_client(provider: Optional[str] = None) -> BaseLLMClient:
    """Factory to create an appropriate LLM client based on configuration."""
    settings = get_settings()
    chosen_provider = (provider or settings.llm_provider).lower()

    if chosen_provider == "mock":
        return MockLLMClient()
    elif chosen_provider in ("openai", "ollama"):
        return OpenAILLMClient()
    else:
        return MockLLMClient()
