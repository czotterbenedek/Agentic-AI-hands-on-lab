# Agentic AI Hands-on Lab

Hands-on laboratory curriculum for the MSc course *AI In Practice (2026)* at Budapest University of Technology and Economics (BME).

Throughout five progressive modules, students build a production-grade **University Research Assistant** from first principles-learning tool execution, open protocols, persistent memory, multi-agent coordination, and automated evaluation.

---

## 📂 Repository Structure

```text
agentic-ai-hands-on-lab/
├── labs/              # Starter code with scaffolded # TODO tags for students
│   ├── 01-tool-calling/   # Lab 1: ReAct loop & JSON Schema function calling
│   ├── 02-mcp/            # Lab 2: Model Context Protocol (MCP) server & client
│   ├── 03-memory/         # Lab 3: SQLite memory hierarchy & user isolation
│   ├── 04-multi-agent/    # Lab 4: LangGraph StateGraph multi-agent consortium
│   └── 05-evaluation/     # Lab 5: Benchmark evaluation & MLflow experiment tracking
├── solutions/         # Complete, independently runnable reference solutions
├── shared/            # Common infrastructure (LLM clients, Tool abstractions, logging)
├── docs/              # Full course documentation and lab sheets (MkDocs)
├── tests/             # Unified test runner and Failure Museum regression tests
├── requirements.txt   # Python dependencies
└── mkdocs.yml         # MkDocs Material configuration
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python **3.11+**
- Git

### 2. Installation
```bash
git clone https://github.com/Agentic-AI-hands-on-lab.git
cd agentic-ai-hands-on-lab

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
cp .env.example .env
```
*Note: By default, `LLM_PROVIDER=mock` is enabled. You can complete all labs and pass 100% of unit tests offline without any API keys or GPU! To use live models, set `LLM_PROVIDER=openai` (with `OPENAI_API_KEY`) or `LLM_PROVIDER=ollama` in `.env`.*

---

## 📚 Curriculum Modules

1. **[Lab 1: Tool Calling & ReAct](docs/01-tool-calling.md)**: Implement the Thought-Action-Observation loop, AST-safe calculator, and citation analytics.
2. **[Lab 2: Model Context Protocol (MCP)](docs/02-mcp.md)**: Build a standalone JSON-RPC 2.0 MCP server, dynamic tool discovery, and stdio client.
3. **[Lab 3: Agent Memory & Personalization](docs/03-memory.md)**: Implement SQLite episodic history, user-isolated preference storage, and prompt context injection.
4. **[Lab 4: Multi-Agent Systems & LangGraph](docs/04-multi-agent.md)**: Build a Supervisor-Specialist hierarchy using LangGraph state machines with 2-cycle loop detection.
5. **[Lab 5: Agent Evaluation & MLflow](docs/05-evaluation.md)**: Measure task success, tool selection F1, latency, and log experiments to MLflow.
6. **[Failure Museum](docs/failure-museum.md)**: Study and test 6 classic agent failure modes (infinite loops, hallucinated tools, bad arguments, connection drops, memory leakage, ping-pong delegation).

---

## 🧑‍💻 How to Work on the Labs

1. Open a starter lab in `labs/<module-number>/` and find the `# TODO [Lab X.Y]` sections.
2. Implement the required logic as described in the docstrings and docs lab sheets.
3. Run the interactive lab runner to see your agent in action:
   ```bash
   python3 labs/01-tool-calling/run_lab.py
   ```
4. Verify your implementation with pytest:
   ```bash
   python3 -m pytest labs/01-tool-calling/test_lab.py
   ```
5. Run the entire reference solution test suite:
   ```bash
   python3 tests/test_all_solutions.py
   ```

---

## 📖 Documentation Site

The complete course documentation, interactive architecture diagrams, and laboratory sheets are hosted on GitHub Pages:

👉 **[https://czotterbenedek.github.io/Agentic-AI-hands-on-lab/](https://czotterbenedek.github.io/Agentic-AI-hands-on-lab/)**

To run and preview the documentation site locally with live reload:
```bash
mkdocs serve
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
