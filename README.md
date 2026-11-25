# Agentic AI Hands-on Lab

Hands-on laboratory curriculum for the MSc course *AI In Practice (2026)* at Budapest University of Technology and Economics (BME).

**Course objective**: Students build a production-grade **University Research Assistant** across five progressive modules—mastering tool execution, open protocols, persistent memory, multi-agent coordination, and automated evaluation.

| Lab | Topic | What you build |
|:---|:---|:---|
| 1 | Tool Calling & ReAct | AST-safe calculator, citation stats, Thought-Action-Observation loop |
| 2 | Model Context Protocol (MCP) | JSON-RPC 2.0 stdio server exposing 5 bibliographic tools + client |
| 3 | Agent Memory & Personalization | SQLite episodic history, per-user preference storage, context injection |
| 4 | Multi-Agent Systems & LangGraph | Supervisor-Specialist StateGraph with 2-cycle loop detection |
| 5 | Agent Evaluation & MLflow | 20-case benchmark, Precision/Recall/F1 for tool use, MLflow tracking |

**Runtime constraints**: Python 3.11+. All labs and tests run fully offline using the built-in `MockLLMClient` (no API key or GPU required). Optional live providers: OpenAI, Ollama, vLLM via `.env`.

**Definition of done**: Each starter lab in `labs/` has a matching reference solution in `solutions/` and a test module. `python3 tests/test_all_solutions.py` reports 6/6 suites passed. `mkdocs build` completes without errors.

---

## 🛠️ Technology Stack

- **Python 3.11+**: Core implementation language.
- **OpenAI Python SDK (`openai>=1.12.0`)**: Standardized model communication supporting OpenAI, Ollama, and vLLM backends.
- **Model Context Protocol (MCP)**: Educational, zero-dependency JSON-RPC 2.0 stdio server and client conforming to Anthropic's open specification.
- **SQLite3 Engine**: ACID-compliant persistent memory with compound primary key schemas and strict per-user privacy isolation.
- **LangGraph StateGraph (`langgraph>=0.2.0`)**: Cyclical state-machine multi-agent orchestration with checkpointers and 2-cycle loop detection.
- **MLflow (`mlflow>=2.10.0`)**: Experiment tracking, parameter logging, and metric visualization.
- **MkDocs Material (`mkdocs-material>=9.5.0`)**: Course documentation with interactive diagrams and dark mode.

---

## 📂 Repository Structure

```text
agentic-ai-hands-on-lab/
├── labs/              # Starter code with guided # TODO tags for students
│   ├── 01-tool-calling/   # Lab 1: ReAct loop & JSON Schema function calling
│   ├── 02-mcp/            # Lab 2: Model Context Protocol (MCP) server & client
│   ├── 03-memory/         # Lab 3: SQLite memory hierarchy & user isolation
│   ├── 04-multi-agent/    # Lab 4: LangGraph StateGraph multi-agent consortium
│   └── 05-evaluation/     # Lab 5: Benchmark evaluation & MLflow experiment tracking
├── solutions/         # Complete, independently runnable reference solutions (100% test pass)
├── shared/            # Common infrastructure (LLM clients, Tool abstractions, logging)
├── docs/              # Full course documentation, lab sheets & Failure Museum (MkDocs)
├── mcp_server/        # Standalone entrypoint shim for Research MCP Server
├── memory/            # Standalone entrypoint shim for SQLite Memory Storage
├── multi_agent/       # Standalone entrypoint shim for Multi-Agent Supervisor
├── evaluation/        # Standalone entrypoint shim for Benchmark Evaluator
├── tests/             # Unified test runner & Failure Museum regression suite
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
git clone https://github.com/czotterbenedek/Agentic-AI-hands-on-lab.git
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
*Note: By default, `LLM_PROVIDER=mock` is enabled. Reference solutions pass 100% of unit tests offline without any API keys or GPU! To use live models, set `LLM_PROVIDER=openai` (with `OPENAI_API_KEY`) or `LLM_PROVIDER=ollama` in `.env`.*

---

## 📚 Curriculum Modules

1. **[Lab 1: Tool Calling & ReAct](docs/01-tool-calling.md)**: Implement the Thought-Action-Observation loop, AST-safe calculator, and citation analytics.
2. **[Lab 2: Model Context Protocol (MCP)](docs/02-mcp.md)**: Build a standalone JSON-RPC 2.0 MCP server exposing 5 bibliographic tools, dynamic tool discovery, and stdio client.
3. **[Lab 3: Agent Memory & Personalization](docs/03-memory.md)**: Implement SQLite episodic history, user-isolated preference storage, and prompt context injection.
4. **[Lab 4: Multi-Agent Systems & LangGraph](docs/04-multi-agent.md)**: Build a Supervisor-Specialist hierarchy using LangGraph state machines with 2-cycle loop detection.
5. **[Lab 5: Agent Evaluation & MLflow](docs/05-evaluation.md)**: Measure task success, tool selection F1, latency, and log experiments to MLflow.
6. **[Failure Museum](docs/failure-museum.md)**: Dissect and test 6 classic agent failure modes (infinite loops, hallucinated tools, bad arguments, connection drops, memory leakage, ping-pong delegation).

---

## 🧑‍💻 How to Work on the Labs

1. Open a starter lab in `labs/<module-number>/` and locate the `# TODO [Lab X.Y]` sections.
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
   *Note: Starter labs in `labs/` contain `NotImplementedError` placeholders for students to complete; the reference implementations in `solutions/` pass all 6 test suites out-of-the-box.*

---

## 📊 Reproducing Evaluation Benchmarks

To reproduce the multi-architecture evaluation benchmark across all four configurations:
```bash
python3 solutions/05-evaluation/run_lab.py
```
This runs the 20-case standardized benchmark, logs parameters and metrics to MLflow (`./mlruns`), and exports `evaluation_benchmark.csv` and `evaluation_benchmark.json`.

---

## 🤖 AI Tools Used & Lessons Learned

- TODO

---

## 📖 Documentation Site

The complete course documentation, interactive architecture diagrams, and laboratory sheets are hosted on GitHub Pages:

👉 **[https://czotterbenedek.github.io/Agentic-AI-hands-on-lab/](https://czotterbenedek.github.io/Agentic-AI-hands-on-lab/)**

To run and preview the documentation site locally with live reload:
```bash
mkdocs serve
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
