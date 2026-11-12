"""Tool definitions, schema generation, and registry for Module 1."""

import inspect
import json
import math
import re
from typing import Any, Callable, Dict, List, Optional, get_type_hints

from shared.agent import Tool


# Curated academic research dataset used consistently across the labs
RESEARCH_PAPERS_DB: List[Dict[str, Any]] = [
    {
        "paper_id": "1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "year": 2017,
        "citations": 125000,
        "abstract": "We propose the Transformer, a model architecture eschewing recurrence and relying entirely on an attention mechanism to draw global dependencies between input and output.",
        "topics": ["transformer", "nlp", "deep learning", "attention"],
    },
    {
        "paper_id": "1810.04805",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        "year": 2018,
        "citations": 85000,
        "abstract": "We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers, designed to pretrain deep bidirectional representations from unlabeled text.",
        "topics": ["nlp", "bert", "transformer", "pretraining"],
    },
    {
        "paper_id": "2106.09685",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "authors": ["Edward J. Hu", "Yelong Shen", "Phillip Wallis", "Zeyuan Allen-Zhu"],
        "year": 2021,
        "citations": 18500,
        "abstract": "We propose Low-Rank Adaptation (LoRA), which freezes the pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture.",
        "topics": ["lora", "fine-tuning", "parameter-efficient", "llm"],
    },
    {
        "paper_id": "2201.11903",
        "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "authors": ["Jason Wei", "Xuezhi Wang", "Dale Schuurmans", "Maarten Bosma"],
        "year": 2022,
        "citations": 12000,
        "abstract": "We explore how generating a chain of thought—a series of intermediate reasoning steps—significantly improves the ability of large language models to perform complex reasoning.",
        "topics": ["prompting", "reasoning", "chain-of-thought", "llm"],
    },
    {
        "paper_id": "2210.03629",
        "title": "ReAct: Synergizing Reasoning and Acting in Language Models",
        "authors": ["Shunyu Yao", "Jeffrey Zhao", "Dian Yu", "Nan Du", "Izhak Shafran", "Karthik Narasimhan"],
        "year": 2022,
        "citations": 7500,
        "abstract": "We explore the use of LLMs to generate both reasoning traces and task-specific actions in an interleaved manner, enabling greater synergy between the two.",
        "topics": ["react", "agent", "reasoning", "tool calling"],
    },
    {
        "paper_id": "2302.04761",
        "title": "Toolformer: Language Models Can Teach Themselves to Use Tools",
        "authors": ["Timo Schick", "Jane Dwivedi-Yu", "Roberto Dessi", "Roberta Raileanu"],
        "year": 2023,
        "citations": 6200,
        "abstract": "Language models can teach themselves to use external tools via simple APIs, deciding which tool to call, when to call it, what arguments to pass, and how to incorporate results.",
        "topics": ["tool calling", "agent", "toolformer", "llm"],
    },
]


def generate_json_schema(func: Callable[..., Any]) -> Dict[str, Any]:
    """Generate a JSON schema for a Python function's parameters from type hints and docstrings."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    properties: Dict[str, Any] = {}
    required: List[str] = []

    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        List[str]: "array",
        List[int]: "array",
        List[Dict[str, Any]]: "array",
    }

    doc = inspect.getdoc(func) or ""
    param_docs: Dict[str, str] = {}
    for line in doc.splitlines():
        line = line.strip()
        match = re.match(r"^:param\s+(\w+):\s*(.+)$", line)
        if match:
            param_docs[match.group(1)] = match.group(2)
        elif line.startswith("- ") and ":" in line:
            parts = line[2:].split(":", 1)
            param_docs[parts[0].strip()] = parts[1].strip()

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue

        param_type = type_hints.get(name, str)
        json_type = type_mapping.get(param_type, "string")
        prop: Dict[str, Any] = {
            "type": json_type,
            "description": param_docs.get(name, f"Parameter `{name}`"),
        }

        if json_type == "array":
            prop["items"] = {"type": "string"}

        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            prop["default"] = param.default

        properties[name] = prop

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


class ToolRegistry:
    """Registry to manage and look up agent tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        func: Optional[Callable[..., Any]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Any:
        """Register a function as a tool. Can be used as a decorator or method."""
        def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or f.__name__
            tool_desc = description or (inspect.getdoc(f) or f"Execute {tool_name}").splitlines()[0]
            schema = generate_json_schema(f)
            self._tools[tool_name] = Tool(
                name=tool_name,
                description=tool_desc,
                parameters=schema,
                func=f,
            )
            return f

        if func is not None:
            return decorator(func)
        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return OpenAI-compatible function calling schemas for all registered tools."""
        return [tool.to_openai_schema() for tool in self._tools.values()]


# ------------------------------------------------------------------------------
# Core Research Assistant Tools
# ------------------------------------------------------------------------------

def calculate(expression: str) -> str:
    """Safely evaluate a mathematical arithmetic expression.

    :param expression: Mathematical expression string, e.g. '125000 / 7' or '18500 + 12000'
    """
    # Allowed tokens: numbers, operators (+, -, *, /, //, %, **), parentheses, and math functions
    cleaned = expression.strip()
    # Security guard: disallow any dangerous built-ins or variable lookups
    if re.search(r"[a-zA-Z_]", cleaned):
        # Allow safe math module functions only
        allowed_names = {"sqrt": math.sqrt, "log": math.log, "pow": math.pow, "abs": abs}
        # Check if the text matches simple allowed function calls
        for fn in allowed_names:
            cleaned = cleaned.replace(fn, "")
        if re.search(r"[a-zA-Z_]", cleaned):
            return "Error: Expression contains forbidden non-mathematical identifiers."

    allowed_locals = {"sqrt": math.sqrt, "log": math.log, "pow": math.pow, "abs": abs}
    try:
        # Compile in eval mode with no globals and restricted locals
        result = eval(expression, {"__builtins__": {}}, allowed_locals)
        if isinstance(result, float):
            result = round(result, 4)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression '{expression}': {e}"


def search_papers(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search academic research papers in the bibliographic database.

    :param query: Keywords or topics to search for, e.g. 'transformer', 'lora', 'agent'
    :param limit: Maximum number of matching papers to return
    """
    query_tokens = [q.lower() for q in re.split(r"\W+", query) if len(q) > 1]
    if not query_tokens:
        query_tokens = [query.lower()]

    matches: List[Dict[str, Any]] = []
    for paper in RESEARCH_PAPERS_DB:
        title_lower = paper["title"].lower()
        abstract_lower = paper["abstract"].lower()
        topics = [t.lower() for t in paper.get("topics", [])]

        score = 0
        for token in query_tokens:
            if token in title_lower:
                score += 3
            if any(token in t for t in topics):
                score += 2
            if token in abstract_lower:
                score += 1

        if score > 0:
            matches.append({**paper, "relevance_score": score})

    # Sort descending by relevance score, then by citation count
    matches.sort(key=lambda p: (p["relevance_score"], p["citations"]), reverse=True)
    return matches[:limit]


def get_paper_details(paper_id: str) -> Dict[str, Any]:
    """Retrieve full bibliographic details for a specific research paper by ID.

    :param paper_id: The identifier of the paper, e.g. '1706.03762'
    """
    for paper in RESEARCH_PAPERS_DB:
        if paper["paper_id"] == str(paper_id).strip():
            return paper
    return {"error": f"Paper with ID '{paper_id}' not found."}


def compute_citation_stats(paper_ids: List[str]) -> Dict[str, Any]:
    """Compute aggregated citation statistics across a list of research papers.

    :param paper_ids: List of paper IDs to aggregate
    """
    citations: List[int] = []
    found_papers: List[str] = []

    for pid in paper_ids:
        paper = get_paper_details(pid)
        if "citations" in paper:
            citations.append(paper["citations"])
            found_papers.append(paper["title"])

    if not citations:
        return {"error": "No valid papers found with given IDs."}

    total = sum(citations)
    avg = total / len(citations)
    return {
        "paper_count": len(citations),
        "total_citations": total,
        "average_citations": round(avg, 2),
        "max_citations": max(citations),
        "min_citations": min(citations),
        "papers": found_papers,
    }


def summarize_paper(paper_id: str) -> str:
    """Generate a structured summary of a research paper's methodology and impact.

    :param paper_id: Paper ID to summarize
    """
    paper = get_paper_details(paper_id)
    if "error" in paper:
        return paper["error"]

    return (
        f"Summary of '{paper['title']}' ({paper['year']}):\n"
        f"Authors: {', '.join(paper['authors'])}\n"
        f"Citations: {paper['citations']:,}\n"
        f"Key Contribution: {paper['abstract']}"
    )


def get_default_tool_registry() -> ToolRegistry:
    """Create and populate a standard tool registry for the University Research Assistant."""
    registry = ToolRegistry()
    registry.register(calculate)
    registry.register(search_papers)
    registry.register(get_paper_details)
    registry.register(compute_citation_stats)
    registry.register(summarize_paper)
    return registry
