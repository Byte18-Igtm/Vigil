# Memory — Supervisor Agent & Subagents Architecture

This document preserves the complete memory of the architecture, implementation steps, design decisions, and verification records for the **Supervisor Agent & Specialized Worker Models (Debugging & Testing)** VS Code extension.

---

## 1. System Vision & Core Principles

The project implements a layered AI-assisted coding environment governed by the following core architectural rules:

1. **Supervisor as Central Orchestrator**:
   * The Supervisor Agent **never executes domain tasks itself**.
   * It is the **only entity** that dispatches tasks to worker subagents and receives their structured responses.
   * It synthesizes the subagent findings into a **verbal verdict** and communicates directly with the developer in the IDE Bot interface.
2. **Two Specialized Worker Models**:
   * **Debugging Model (`DebugAgent`)**: Receives instructions from the Supervisor or Developer. Detects bugs, provides **technical justifications**, executes automated **code maintenance checks**, assigns a **code health rating**, and proposes safe fixes requiring explicit permission.
   * **Testing Model (`TestAgent`)**: Receives instructions from the Supervisor or Developer. Formulates test scenarios, boundary/edge cases, expected behaviors, and verified pytest test suites.
   * Subagents communicate **strictly with the Supervisor**, never directly modifying code without permission.
3. **IDE-Only Bot Interface**:
   * All interactions take place natively inside the VS Code editor:
     * Subtle `🔵` circle markers next to lines with CodeLens and Hover tooltips.
     * Dedicated **Side Bot Webview panel** in the VS Code sidebar featuring an Antigravity visual constellation, real-time activity status, developer prompt dock, verbal speech bubbles, and action cards.
4. **No Hardcoded Mock Data**:
   * The engine integrates real Python AST static inspection and supports Google Gemini / OpenAI / Ollama LLM execution, grounding all analyses in actual code syntax and semantics.

---

## 2. Directory Structure & File Map

```text
d:\Subagents/
├── .venv/                                # Python Virtual Environment (Python 3.14 / pip)
├── requirements.txt                     # Dependencies: fastapi, uvicorn, pydantic, requests, pytest
├── memory.md                            # Comprehensive project memory and change log
├── README.md                            # Architecture & user manual
├── run_server.py                        # FastAPI Server entry point on port 8765
│
├── supervisor_core/                     # Core Python Agent Engine
│   ├── protocol/
│   │   ├── agent_types.py               # Typed Pydantic models: AgentTask, AgentResult, SupervisorEvent
│   │   └── messages.py                  # Typed Webview & Extension message models
│   ├── agents/
│   │   ├── base_agent.py                # Abstract BaseWorkerAgent class
│   │   ├── debug_agent.py               # Debugging Model (justification, maintenance, permission fix)
│   │   ├── test_agent.py                # Testing Model (test scenarios, edge cases, pytest generator)
│   │   └── explain_agent.py             # ExplainAgent implementation
│   ├── supervisor/
│   │   ├── supervisor_agent.py          # Central Orchestrator Agent
│   │   ├── task_manager.py              # Task lifecycle & result registry
│   │   └── event_log.py                 # Structured timeline event logger
│   ├── llm/
│   │   ├── engine.py                    # Multi-provider LLM engine (Gemini/OpenAI/Ollama + AST fallback)
│   │   └── ast_analyzer.py              # Real Python/JS AST parser and maintenance checker
│   ├── server/
│   │   └── api_server.py                # FastAPI endpoints for IDE extension (/api/task, /api/marker, etc.)
│   └── cli.py                           # Interactive CLI tool with UTF-8 Windows terminal support
│
├── extension/                           # VS Code Extension (Layer 1 UI)
│   ├── package.json                     # Extension manifest, commands, sidebar views, keybindings
│   ├── extension.js                     # Extension entry point, command dispatcher & lifecycle manager
│   ├── decorations/
│   │   └── codeMarkerProvider.js        # 🔵 Marker decorations, CodeLens, Hover, QuickPick menu
│   ├── webview/
│   │   ├── sideBotView.js               # WebviewViewProvider for Side Bot
│   │   └── sideBotHtml.js               # IDE Side Bot UI: HTML/CSS/JS & Antigravity constellation
│   ├── client/
│   │   └── supervisorClient.js          # HTTP client bridging extension to Python backend
│   └── utils/
│       └── codeContext.js               # VS Code document context extractor
│
└── tests/
    ├── test_agents.py                   # Automated Pytest suite (7/7 tests passing)
    ├── test_client.js                   # Node.js integration verification test
    └── sample_code.py                   # Sample file for markers and testing
```

---

## 3. Detailed Component Breakdown

### A. Protocol Layer (`supervisor_core/protocol/`)
* **`AgentTask`**: Captures `id`, `type` (`"debug"` | `"test"` | `"explain"`), `filePath`, `line`, `column`, `selectedCode`, `surroundingCode`, `language`, `instruction` (custom instruction), and `source` (`"developer"` | `"supervisor"`).
* **`DebugAgentPayload`**:
  * `detectedIssue`: Name and description of the bug or risk.
  * `evidenceReasoning`: Why the pattern fails at runtime.
  * `possibleCause`: Underlying mechanism or root cause.
  * `justification`: **Technical rationale** explaining why this is a flaw and why this fix is the optimal approach.
  * `maintenanceChecks`: List of automated maintenance check findings.
  * `maintenanceScore`: Overall health rating (`"clean"` | `"moderate_debt"` | `"high_risk"`).
  * `maintenanceRecommendations`: Proactive recommendations for codebase longevity.
  * `suggestedFix`: Code replacement or proposed diff.
  * `requiresPermission`: Strict boolean flag requiring explicit developer confirmation before applying.
* **`TestAgentPayload`**:
  * `whatShouldBeTested`: Scope and critical behaviors.
  * `testCases`: Concrete test scenarios with inputs and expected outcomes.
  * `edgeCases`: Boundary constraints and error conditions.
  * `expectedBehavior`: Specification of expected behavior.
  * `generatedTestCode`: Ready-to-run pytest code.
  * `executionResult`: Verification status of the generated test code.
* **`SupervisorEvent`**:
  * Timestamped timeline event: `id`, `type`, `taskId`, `agent`, `filePath`, `line`, `message`, `status` (`"info"`, `"running"`, `"success"`, `"error"`).

---

### B. Supervisor Agent (`supervisor_core/supervisor/`)
* **`SupervisorAgent`**:
  * Dispatches structured tasks to registered worker models.
  * Automatically sets task origin (`developer` or `supervisor`).
  * Enforces that worker responses return strictly to the Supervisor.
  * **Verbal Synthesis**: Formulates conversational responses for the developer:
    > *"In response to your instruction ('Verify division by zero'), I had DebugAgent (debugging model) inspect sample_code.py:13. Diagnosis: 'Defensive execution check on line 13' (medium confidence, Code Health: Moderate Debt). Justification: Wrapping unguarded operations... Review the technical justification, maintenance checks, and proposed fix below before granting permission to apply."*
* **`SupervisorEventLog`**:
  * Thread-safe chronological event tracking with subscriber event notifications.
* **`TaskManager`**:
  * Maps task IDs to tasks and completed results.

---

### C. Worker Models & Static AST Analysis (`supervisor_core/agents/` & `supervisor_core/llm/`)
* **`DebugAgent` (Debugging Model)**:
  * Analyzes code against developer instructions or autonomous safety rules.
  * Identifies syntax errors, unhandled exceptions, zero-division, mutable default arguments, bare excepts, and boundary flaws.
  * Formulates engineering **justification** and runs **maintenance checks**.
  * Never modifies code automatically.
* **`TestAgent` (Testing Model)**:
  * Analyzes target functions and generates executable test suites.
  * Tailors test scenarios to developer instructions (e.g. testing negative values).
  * Validates test code syntax.
* **`CodeStaticAnalyzer`**:
  * Python AST visitor extracting functions, classes, calls, imports, variables, and potential bug patterns.
  * **`run_maintenance_checks`**:
    1. *Type Annotations Audit*: Checks parameter and return type hints (PEP 484).
    2. *Documentation Coverage*: Audits docstrings on declared functions.
    3. *Antipattern Detection*: Catches mutable defaults (`arg=[]`), bare excepts.
    4. *Resource Safety*: Audits context managers (`with` blocks) for file/socket I/O.
    5. *Architecture Integrity*: Checks for `global` keyword mutations.
    6. *JavaScript/TypeScript Checks*: Strict equality (`===`), production `console.log` detection.
    7. *Health Score*: Computes `clean`, `moderate_debt`, or `high_risk`.

---

### D. IDE Bot Interface (`extension/`)
* **`sideBotView.js` & `sideBotHtml.js`**:
  * Sidebar Webview registered as `supervisor.sideBotView`.
  * **Antigravity Constellation Header**: Interactive architecture visual:
    `Debugging Model <— Supervisor Orchestrator —> Testing Model`
  * **Developer Input Dock**: Bottom bar where the developer can:
    * Select target model: `🐞 Debug` or `🧪 Test`.
    * Type custom instructions.
    * Click quick action chips: `🐞 Debug Active Line`, `🧪 Test Active Line`, `🔵 Mark Line`, `⚡ Clear`.
  * **Supervisor Verbal Speech Bubble**: Conversational verdicts spoken directly to the developer.
  * **💡 Technical Justification Card**: Highlights engineering rationale.
  * **🛡️ Code Maintenance Box**: Renders the health badge, maintenance audit checklist, and recommendations.
  * **✓ Apply Fix**: Prompts a VS Code modal confirming permission before writing modifications to disk.
  * **📋 Copy Test Suite**: One-click clipboard copy of the generated pytest suite.
* **`codeMarkerProvider.js`**:
  * Toggles `🔵` markers on any line (`Alt + M` or right-click context menu).
  * Shows CodeLens: `🔵 Supervisor: Debug | Test`.
  * Shows Hover tooltip with direct command links.
* **`supervisorClient.js`**:
  * Bridges VS Code Extension to the Python FastAPI backend on `http://127.0.0.1:8765`.
  * Auto-starts the Python backend from `.venv` if not currently running.

---

## 4. Chronological Change Log & Evolution

| Step | Action Taken | Rationale / Prompt Requirement |
|---|---|---|
| **1** | Set up Python virtual environment (`.venv`) and installed dependencies | User requested: *"create an python environment and do in that"*. |
| **2** | Designed typed protocol (`AgentTask`, `AgentResult`, `SupervisorEvent`) | Core requirement: Structured typed protocol, no random strings. |
| **3** | Built AST Static Code Analyzer & Intelligence Engine (`ast_analyzer.py`, `engine.py`) | Core requirement: No hardcoded fake data; real code intelligence with LLM support & AST fallback. |
| **4** | Implemented Worker Agents (`DebugAgent`, `TestAgent`, `ExplainAgent`) | Specialized workers returning structured outputs. |
| **5** | Implemented Central Supervisor Orchestrator (`SupervisorAgent`, `event_log.py`, `task_manager.py`) | Supervisor delegates tasks, maintains history, and synthesizes verbal verdicts. |
| **6** | Built VS Code Extension (Markers, CodeLens, Side Bot Webview, Client) | Layer 1 IDE integration with 🔵 circle markers and sidebar Bot. |
| **7** | Refocused on **Two Models (Debugging & Testing)** receiving instructions from Supervisor or Developer | User request: *"i want two models debugging and testing that receives instruction from supervisor or developer and sends response to supervisor."* |
| **8** | Added Interactive Developer Instruction Dock in Side Bot | Enabled developer to type custom prompts into the IDE Bot panel. |
| **9** | Removed standalone web UI to focus strictly on IDE | User request: *"no need for a side bot in web just in IDE is enough"*. |
| **10** | Added **Technical Justification** to Debugging Model | User request: *"the debugging agent should also justify"*. |
| **11** | Added Automated **Code Maintenance Checks** & Health Ratings | User request: *"and do maintainance checks"*. |
| **12** | Integrated Justification & Maintenance UI cards into IDE Side Bot | Provided rich visual presentation for justification, health score, and checklist items. |
| **13** | Built and executed Pytest verification suite (7/7 tests passed) | Rigorous verification of all models, instructions, and Supervisor orchestration. |

---

## 5. Verification Records

### Automated Pytest Test Suite
Executed in `.venv`:
```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe -m pytest tests/test_agents.py -v
```

**Results: 7 Passed, 0 Failed (100% Success)**
* `test_supervisor_registration`: PASSED
* `test_explain_agent_execution`: PASSED
* `test_debug_agent_execution`: PASSED (verifies suggested fix, permission gate, justification, and maintenance checks)
* `test_test_agent_execution`: PASSED (verifies test cases, edge cases, and generated code)
* `test_event_history_tracking`: PASSED (verifies marker creation, request receipt, dispatch, and completion events)
* `test_developer_instruction_to_debugging_model`: PASSED (verifies custom developer prompt passed through to Debugging Model)
* `test_developer_instruction_to_testing_model`: PASSED (verifies custom developer prompt passed through to Testing Model)

---

## 6. How to Launch and Test

1. **Open the workspace in VS Code**:
   * Open `d:\Subagents`.
2. **Launch the Extension**:
   * Press `F5` (or click `Run and Debug` -> `Run Extension`).
   * A new Extension Development Host window will open.
3. **Open a code file**:
   * Open `tests/sample_code.py` or any file.
4. **Interact via Editor Marker**:
   * Place the cursor on any line and press `Alt + M` (or right-click `Supervisor: Mark Line 🔵`).
   * A `🔵` marker appears in the gutter and beside the line.
   * Choose `🐞 Debugging Model`, `🧪 Testing Model`, or `Custom Instruction`.
5. **Interact via Side Bot Panel**:
   * Open the **Supervisor Agent** icon in the Activity Bar.
   * Type any instruction in the bottom dock (e.g. *"Check if this handles zero division"*).
   * Observe the Antigravity pulse, the Supervisor's verbal verdict, the technical justification, the code maintenance checklist, and the permission-gated fix button.
