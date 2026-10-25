# 🎓 AcadOps — AI-Powered Academic Operations Assistant

**From managing tasks to making smarter academic decisions.**

AcadOps is an AI-powered academic planning assistant designed to help students understand their workload, prioritize deadlines, identify potential conflicts, and decide what to work on next.

Instead of acting as just another to-do list, AcadOps combines academic task information with decision-making logic to provide actionable planning guidance.

> **Our guiding question:** Given everything happening right now, what should I do next — and why?

## 🎯 The Problem

Students manage assignments, examinations, projects, presentations, and multiple deadlines simultaneously. Traditional task managers can store these commitments, but they often leave students to decide which task matters most, how much work remains, and whether their available study time is sufficient.

AcadOps aims to bridge that gap by turning academic workload information into structured decisions and adaptive plans.

## ✨ Key Features

- **🧠 Intelligent Task Prioritization** — Helps identify the next academic task based on urgency, deadlines, and remaining work.
- **📊 Workload Risk Analysis** — Evaluates academic workload against available study time to highlight potential pressure.
- **🔄 Adaptive Replanning** — Supports updating study plans when task progress or priorities change.
- **⚠️ Conflict Detection** — Identifies potential conflicts between academic commitments.
- **💬 Natural-Language Chat** — Lets students ask questions about tasks, deadlines, progress, and workload.
- **📈 Progress Tracking** — Supports task-progress updates and completion tracking.
- **🗂️ Planning History** — Persists previous plans so students can review planning decisions.
- **🔌 MCP Integration** — Includes an MCP server for exposing AcadOps functionality to compatible AI clients.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and decision logic |
| Flask | Web application and HTTP routes |
| SQLite | Persistent storage for tasks, settings, and planning history |
| HTML | Dashboard and history interfaces |
| Model Context Protocol (MCP) | Integration with compatible AI clients |

## 🏗️ Project Architecture

AcadOps follows a modular architecture that separates application routing, data storage, academic decision-making, and user interaction.

```text
AcadOps
│
├── app.py                  # Flask application and routes
├── database.py             # Persistent data storage
├── academic_state.py       # Academic workload state
├── acadops_agent.py        # Academic assistant coordination
│
├── decision_engine.py      # Task prioritization
├── risk_engine.py          # Workload risk analysis
├── conflict_engine.py      # Conflict detection
├── adaptive_replanner.py   # Plan adjustment
│
├── chat_engine.py          # Natural-language interaction
├── mcp_server.py           # MCP integration
├── test_mcp.py             # MCP test script
│
├── dashboard.html          # Dashboard interface
├── history.html            # Planning history interface
└── templates/
    └── dashboard.html      # Flask dashboard template
```

## ⚙️ Getting Started

### Prerequisites

- Python 3.11 or a compatible Python version
- Git
- A terminal such as PowerShell on Windows

### 1. Clone the repository

```bash
git clone https://github.com/MansiBavaliya/acadops.git
cd acadops
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the packages required by the project. If a `requirements.txt` file is available, run:

```powershell
pip install -r requirements.txt
```

If that file has not been created yet, install the dependencies listed in your project's imports and document them in a `requirements.txt` file before asking others to run the project.

### 4. Run AcadOps

Start the Flask application:

```powershell
python app.py
```

Open the local address displayed in your terminal, typically:

```text
http://127.0.0.1:5000
```

**Note:** Confirm the project's dependency list and startup configuration before publishing these setup instructions as fully tested.

## 🧪 Testing and Validation

The repository includes `test_mcp.py` for testing MCP interactions.

Run the test using the project's configured Python environment:

```powershell
python test_mcp.py
```

Ensure the required MCP server and dependencies are configured before running the test.

## 🔐 Data and Privacy

AcadOps uses SQLite for persistent academic data. The local database and backup files should remain excluded from version control.

The repository's `.gitignore` excludes database files, virtual environments, cache files, and common backup files. Keep credentials and environment-specific secrets out of public commits.

## 🚀 Future Improvements

- More accurate and personalized task prioritization
- Improved workload visualizations and progress summaries
- More comprehensive automated tests
- Stronger follow-up handling in the chat assistant
- Further validation of MCP integration
- More personalized adaptive study planning

## 🏆 What Makes AcadOps Different?

AcadOps focuses on the **decision behind the task**. Rather than simply showing students what is pending, it aims to help them understand urgency, workload, and the next useful action.

The long-term vision is to build a dependable academic operations assistant that helps students plan realistically, respond to changing deadlines, and make more informed study decisions.

## 👩‍💻 Built With

Developed as a student project exploring AI-assisted academic planning, modular decision systems, and MCP-based integration.

## 📄 License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
