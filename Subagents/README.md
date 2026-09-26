# Supervisor Agent — VS Code AI Coding Assistant

A professional VS Code extension implementing the **Supervisor Agent + Two Worker Models (Debugging Model & Testing Model)** architecture with the Antigravity visual identity.

The developer can mark any line of code with a small 🔵 circle or type instructions directly into the **IDE Side Bot Panel**. The central **Supervisor Agent** coordinates the appropriate worker model (**Debugging Model** or **Testing Model**), receives its response, and verbally communicates the conclusion back to the developer in the IDE Bot interface.

---

## 1. System Architecture

```text
               ┌─────────────────┐
               │ Debugging Model │
               └────────┬────────┘
                        │ (subagent response)
                        │
                        ▼
             ┌─────────────────────┐
             │   Supervisor Agent  │◄── Instructions from Developer / Markers
             │    (Orchestrator)   │──► Tasks to Worker Models
             └──────────┬──────────┘
                        │ (subagent response)
                        │
                        ▼
               ┌─────────────────┐
               │  Testing Model  │
               └─────────────────┘
                        │
                        ▼ (Verbal verdict & conclusions)
             ┌─────────────────────┐
             │ VS Code IDE Side Bot│
             │   (Bot Interface)   │
             └─────────────────────┘
```

### Layer 1 — VS Code IDE Bot Interface (`extension/`)
- **IDE-Only Bot Panel (`sideBotView.js` & `sideBotHtml.js`)**:
  - Resides natively inside VS Code's Activity Bar sidebar.
  - Interactive **Developer Input Dock**: Type any custom instruction (e.g., *"Check if this function handles empty lists"*, *"Generate pytest cases for edge cases with negative values"*).
  - Target model selector: `🐞 Debugging Model` or `🧪 Testing Model`.
  - Quick action chips: `🐞 Debug Active Line`, `🧪 Test Active Line`, `🔵 Mark Line`, `⚡ Clear`.
  - **Antigravity Constellation**: Visual indicator showing active worker model transitions (`Debugging <— Supervisor —> Testing`).
  - **Supervisor Verbal Dialogue**: Supervisor speaks verbally to the developer before displaying model cards.
  - **Permission-Gated Fix Button**: Debugging Model's proposed fix requires developer confirmation before modifying files.
  - **Copy Test Suite**: Testing Model's ready-to-run pytest code with one-click copy.
- **Code Decorations (`codeMarkerProvider.js`)**:
  - Small unobtrusive `🔵` marker next to selected lines and in the gutter.
  - CodeLens (`🔵 Supervisor: Debug | Test`) and Hover tooltip with direct command links.

### Layer 2 — Supervisor Agent (`supervisor_core/supervisor/`)
- Central orchestrator receiving instructions either autonomously from editor markers or directly from developer prompts.
- Packages structured tasks (`AgentTask`) with code context (file, line, surrounding lines, language, custom instruction, and source).
- Worker models send responses **only to the Supervisor**.
- Supervisor synthesizes the response into a **verbal message** for the developer:
  > *"In response to your instruction ('Verify division by zero'), I had DebugAgent (debugging model) inspect sample_code.py:13. It concluded: ... Please review before granting permission to apply."*
- Maintains a structured event timeline (`SupervisorEvent`).

### Layer 3 — Two Specialized Worker Models (`supervisor_core/agents/`)
- **1. Debugging Model (`DebugAgent`)**:
  - Analyzes code context and developer instructions.
  - Identifies bugs, syntax errors, boundary risks, and possible root causes.
  - **Technical Justification**: Explains the engineering rationale for the diagnosis and justifies why the specific fix is optimal compared to alternatives.
  - **Code Health & Maintenance Checks**: Runs automated maintenance audits on technical debt, type annotation completeness, docstring coverage, resource safety, and antipatterns (bare excepts, mutable defaults, loose equality).
  - **Preventative Recommendations**: Proposes actionable advice for long-term codebase maintainability.
  - **Suggested Fix with Permission Gate**: Strictly requires developer approval before applying code changes.
- **2. Testing Model (`TestAgent`)**:
  - Formulates unit tests, edge cases, and expected behaviors.
  - Generates ready-to-run pytest test suites.
  - Verifies test code syntax and readiness.

---

## 2. Directory Structure

```text
d:\Subagents/
├── .venv/                         # Python Virtual Environment
├── requirements.txt               # Dependencies (FastAPI, Uvicorn, Pydantic, Pytest, Requests)
├── run_server.py                  # Backend API Server entry point (port 8765)
│
├── supervisor_core/               # Python Supervisor & Subagents Engine
│   ├── protocol/
│   │   ├── agent_types.py         # AgentTask, AgentResult, SupervisorEvent models
│   │   └── messages.py            # Centralized Webview/Extension messages
│   ├── agents/
│   │   ├── base_agent.py          # Abstract BaseWorkerAgent class
│   │   ├── debug_agent.py         # Debugging Model implementation
│   │   └── test_agent.py          # Testing Model implementation
│   ├── supervisor/
│   │   ├── supervisor_agent.py    # SupervisorAgent orchestrator
│   │   ├── task_manager.py        # Task lifecycle & result store
│   │   └── event_log.py           # Structured event timeline
│   ├── llm/
│   │   ├── engine.py              # LLM client & AST static code analysis
│   │   └── ast_analyzer.py        # Python/JS AST parser
│   └── server/
│       └── api_server.py          # FastAPI REST endpoints for IDE extension
│
├── extension/                     # VS Code Extension (Layer 1 UI)
│   ├── package.json               # Extension manifest, commands & views
│   ├── extension.js               # Extension controller & command router
│   ├── decorations/
│   │   └── codeMarkerProvider.js  # 🔵 Marker decorations, CodeLens & Hover
│   ├── webview/
│   │   ├── sideBotView.js         # WebviewViewProvider for Sidebar
│   │   └── sideBotHtml.js         # Native IDE Side Bot UI HTML/CSS/JS
│   ├── client/
│   │   └── supervisorClient.js    # Client bridging extension to Python backend
│   └── utils/
│       └── codeContext.js         # Editor context extractor
│
└── tests/
    ├── test_agents.py             # Pytest automated test suite (7/7 passed)
    └── sample_code.py             # Code sample for marker & agent testing
```

---

## 3. Running & Verifying

### Run Automated Tests in the Python Environment
```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m pytest tests/test_agents.py -v
```
*(All 7 test suites pass)*

### Run the Extension in VS Code
1. Open `d:\Subagents` in VS Code.
2. Press `F5` to open the **Extension Development Host**.
3. Open any file (such as `tests/sample_code.py`).
4. Click the **Supervisor Agent** icon in the Activity Bar to reveal the **Side Bot Panel**.
5. In the Side Bot:
   - Select `🐞 Debug` or `🧪 Test`.
   - Type any instruction in the input bar and press Enter (or click quick chips).
   - Or press `Alt + M` to mark a line with `🔵`.
6. Watch the Supervisor coordinate the chosen model, display the Antigravity pulse, deliver the verbal verdict, and show the action buttons.
