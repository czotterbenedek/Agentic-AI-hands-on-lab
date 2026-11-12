# Implementation Plan – Agentic AI Hands-on Lab

## 1. Project objective

Create a complete, publicly accessible educational lab for the BME MSc course *AI In Practice – 2026*, covering practical Agentic AI development.

The project must teach students how to build, understand, evaluate and debug AI agents through five progressive hands-on modules.

The central example throughout the course will be a **University Research Assistant** that can search research papers, analyze information, remember user preferences and delegate tasks to specialist agents.

The implementation must fit the assignment's 15–20-hour student workload.

## 2. Technology stack

- Python 3.11+
- Ollama or an OpenAI-compatible API for LLM inference
- Python OpenAI SDK for model communication
- Custom lightweight ReAct agent implementation
- Official Python MCP SDK for MCP server development
- SQLite for persistent memory
- Pydantic for structured data and validation
- pytest for testing
- pandas for evaluation and experiment analysis
- MkDocs Material for educational documentation
- GitHub Pages for deployment

Keep dependencies and implementation complexity minimal. Avoid introducing unnecessary frameworks.

The LLM provider and model must be configurable through environment variables. Never hardcode API keys.

## 3. Repository structure

Create the following structure:

```text
agentic-ai-hands-on-lab/
├── docs/
│   ├── index.md
│   ├── 01-tool-calling.md
│   ├── 02-mcp.md
│   ├── 03-memory.md
│   ├── 04-multi-agent.md
│   ├── 05-evaluation.md
│   └── failure-museum.md
├── labs/
│   ├── 01-tool-calling/
│   ├── 02-mcp/
│   ├── 03-memory/
│   ├── 04-multi-agent/
│   └── 05-evaluation/
├── solutions/
│   ├── 01-tool-calling/
│   ├── 02-mcp/
│   ├── 03-memory/
│   ├── 04-multi-agent/
│   └── 05-evaluation/
├── shared/
│   ├── llm_client.py
│   ├── agent.py
│   ├── config.py
│   └── logging.py
├── mcp_server/
│   └── server.py
├── memory/
│   └── storage.py
├── multi_agent/
│   ├── supervisor.py
│   ├── research_agent.py
│   └── analysis_agent.py
├── evaluation/
│   ├── test_cases.json
│   ├── evaluate.py
│   └── metrics.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── mkdocs.yml
└── README.md
```

## 4. Implementation modules

### Module 1 – Tool Calling and ReAct

Teach students how LLM agents interact with external tools.

Implement:
- A basic LLM client.
- A lightweight custom ReAct agent loop.
- Tool registration and execution.
- Function/tool calling with structured arguments.
- At least two tools:
  - Calculator.
  - Research paper search.
- Tool result handling and final answer generation.
- Maximum iteration limit to prevent infinite loops.
- Basic error handling and execution logging.

Explain the Thought → Action → Observation → Final Answer workflow. Make clear that internal model reasoning is not exposed; use observable tool calls and results to teach the loop.

Student exercise: Extend the agent with an additional tool and solve a multi-step research question.

### Module 2 – Model Context Protocol (MCP)

Teach students how to expose external capabilities through MCP.

Implement:
- A standalone MCP server using the official Python MCP SDK.
- Three tools:
  - `search_papers(query)`
  - `get_paper_details(paper_id)`
  - `get_recent_papers(topic)`
- A client that connects the research agent to the MCP server.
- Tool discovery and invocation.
- Error handling for unavailable servers and invalid arguments.

Use Crossref or another suitable public bibliographic API. Include a small local fallback dataset for reliable exercises.

Student exercise: Add a new MCP tool and make the agent use it.

### Module 3 – Agent Memory

Teach the difference between conversation history and persistent memory.

Implement:
- Short-term conversation history.
- Persistent SQLite storage.
- Saving and retrieving user preferences.
- User-specific memory isolation.
- Memory retrieval and injection into the agent context.
- A way to inspect and clear stored memories.

Student exercise: Build an assistant that remembers a student's research interests and uses them to personalize paper recommendations.

### Module 4 – Multi-Agent Systems and Handoff

Teach delegation between specialized agents.

Implement:
- A supervisor agent.
- A Research Agent responsible for finding papers.
- An Analysis Agent responsible for analyzing retrieved information.
- Explicit handoff between agents.
- Structured task inputs and outputs.
- A shared execution context.
- Execution traces showing delegation and results.
- Maximum delegation depth and iteration limits to prevent infinite handoffs.

Student exercise: Make the supervisor delegate a research question to the appropriate specialists and combine their results.

### Module 5 – Agent Evaluation

Build a reproducible evaluation framework.

Create a dataset of approximately 20 test tasks covering all implemented capabilities.

Measure:
- Task success rate.
- Tool selection accuracy.
- Tool execution success rate.
- Average number of execution steps.
- Average latency.
- Token usage, when available.

Compare the following configurations:
1. Basic LLM without tools.
2. Single agent with tools.
3. Single agent with tools and memory.
4. Multi-agent implementation.

Implement:
- Evaluation dataset in JSON.
- Automated test execution.
- Metrics calculation.
- CSV or JSON result export.
- Comparison tables and visualizations.
- A short analysis explaining the results and limitations.

Use deterministic checks wherever possible. Do not rely exclusively on an LLM judge.

Student exercise: Improve one agent configuration and demonstrate measurable improvements.

## 5. Failure Museum

Create a dedicated educational section documenting at least six agent failure scenarios.

Include:
1. Infinite ReAct loop.
2. Hallucinated or nonexistent tool.
3. Incorrect tool arguments.
4. MCP server connection failure.
5. Incorrect or contaminated memory.
6. Multi-agent delegation loop or failure.

For each failure, provide:
- Scenario and example input.
- Observable agent behavior.
- Root cause.
- Reproduction instructions.
- Recommended fix.
- A regression test demonstrating that the fix works.

Use runnable examples where practical rather than purely theoretical descriptions.

## 6. Educational materials

Each module must have a corresponding lab sheet containing:

1. Learning objectives.
2. Short theoretical introduction.
3. Architecture explanation.
4. Step-by-step setup instructions.
5. Guided coding exercise.
6. Independent student task.
7. Expected output.
8. Troubleshooting section.
9. Further reading and references.

The `labs/` directory must contain incomplete starter implementations with clearly marked TODO sections.

The `solutions/` directory must contain complete, independently runnable reference implementations.

Keep the educational explanations accessible to MSc students with basic Python and machine learning knowledge.

## 7. Website and deployment

Use MkDocs Material to publish the educational materials.

The website must include:
- Project introduction.
- Navigation for all five modules.
- Code examples and exercises.
- Reference solutions.
- Failure Museum.
- Evaluation methodology and results.
- Installation and usage instructions.

Deploy the documentation using GitHub Pages.

A frontend chat application is optional. Prioritize functional agent implementations and educational quality over frontend complexity.

## 8. Testing and quality requirements

- Every module must have runnable examples.
- Add pytest tests for critical functionality.
- Test tool execution, invalid arguments, memory persistence, agent handoffs and evaluation metrics.
- Include sensible error messages.
- Ensure that the project works with the documented setup instructions.
- Keep API credentials out of source control.
- Include `.env.example`.
- Provide a reproducible evaluation procedure.
- Verify that reference solutions work independently.

## 9. README requirements

The README must explain:
- Project purpose and learning objectives.
- Technology stack.
- Repository structure.
- Installation and configuration.
- How to run each module.
- How to run tests.
- How to reproduce evaluation experiments.
- Deployment URL.
- AI coding tools and agents used during development.
- Important prompts and examples of generated code that required manual correction.
- Lessons learned.

## 10. Implementation strategy

Implement incrementally in the following order:

1. Initialize repository, virtual environment, configuration and LLM client.
2. Implement and test the ReAct agent.
3. Build the MCP server and client integration.
4. Implement persistent memory.
5. Implement the supervisor and specialist agents.
6. Build the evaluation framework and run experiments.
7. Implement failure scenarios and regression tests.
8. Write lab sheets and reference solutions.
9. Build and deploy the MkDocs website.
10. Complete README and verify the entire project from a clean environment.

After each milestone:
- Run relevant tests.
- Verify the implementation.
- Update documentation.
- Keep the repository in a working state.

Do not implement everything in one large code-generation step.

## 11. Scope and priorities

The primary objective is a complete, runnable educational lab, not a production-grade agent platform.

Prioritize:
1. Correct and understandable implementations.
2. Practical exercises.
3. Reproducible evaluation.
4. Meaningful failure demonstrations.
5. Clear documentation.

Avoid:
- Unnecessary frontend development.
- Complex vector databases.
- Expensive proprietary APIs.
- Overengineered orchestration frameworks.
- Features that do not contribute directly to the learning objectives.

Make reasonable technical decisions independently, document them, and keep the total implementation aligned with the 15–20-hour assignment scope.

**Start by inspecting the repository, creating the project structure and implementing Milestone 1 only. Do not proceed to subsequent milestones until the current milestone is working and tested.**