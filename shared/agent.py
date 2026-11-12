"""Base models and abstract classes for tools and agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolCall:
    """Represents a tool call requested by the model."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class Message:
    """Represents a message in the conversation / ReAct context."""
    role: str  # "system", "user", "assistant", "tool"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary compatible with OpenAI API."""
        msg: Dict[str, Any] = {"role": self.role}
        if self.content is not None:
            msg["content"] = self.content
        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": (
                            tc.arguments
                            if isinstance(tc.arguments, str)
                            else __import__("json").dumps(tc.arguments)
                        ),
                    },
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        if self.name:
            msg["name"] = self.name
        return msg


@dataclass
class Tool:
    """Represents an executable tool exposed to agents."""
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable[..., Any]

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert tool definition to OpenAI function call format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool function with provided keyword arguments."""
        return self.func(**kwargs)


@dataclass
class AgentResponse:
    """Structured response returned by an agent step or LLM call."""
    content: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: Optional[str] = None
    raw: Any = None


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def run(self, user_query: str, **kwargs: Any) -> str:
        """Execute the agent on a user query and return the final answer."""
        pass
