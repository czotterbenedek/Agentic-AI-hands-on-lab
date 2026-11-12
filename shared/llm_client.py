"""LLM Client implementations: Base interface, OpenAI/Ollama client, and MockLLMClient."""

import json
import re
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from shared.agent import AgentResponse, Message, ToolCall
from shared.config import Settings, get_settings


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
    """Client for OpenAI and OpenAI-compatible endpoints (such as Ollama or VLLM)."""

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

    def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> AgentResponse:
        """Send completion request to the OpenAI-compatible REST endpoint."""
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
                    citations = re.findall(r'(\d+)\s+citations', obs_content)
                if citations:
                    expr = " + ".join(citations[:3])
                    return AgentResponse(
                        content="I have found the papers. Now I will calculate their total citations.",
                        tool_calls=[
                            ToolCall(
                                id=f"mock_call_{self.call_count}",
                                name="calculate",
                                arguments={"expression": expr},
                            )
                        ],
                    )

            # Otherwise synthesize final answer from observation
            return AgentResponse(
                content=f"Based on the tool results: {obs_content}",
                tool_calls=[],
                finish_reason="stop",
            )

        # 2. If last message is from user (or assistant without tools yet), determine if tools are needed
        user_content = ""
        for m in reversed(messages):
            if m.role == "user" and m.content:
                user_content = m.content
                break

        query = user_content.lower()

        # Paper search query (prioritize search if query mentions papers/search)
        if ("paper" in query or "research" in query or "search" in query or "arxiv" in query) and "search_papers" in available_tools:
            topic = "transformer"
            for t in ["lora", "diffusion", "bert", "attention", "reinforcement", "agent", "rag"]:
                if re.search(rf"\b{t}\b", query):
                    topic = t
                    break
            return AgentResponse(
                content=f"I should search the literature for papers on '{topic}'.",
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
