import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..protocol.agent_types import AgentResult, SupervisorEvent
from ..supervisor.supervisor_agent import SupervisorAgent

supervisor = SupervisorAgent()

app = FastAPI(
    title="Supervisor Agent Backend",
    description="Central Orchestrator coordinating Debugging and Testing Worker Models for VS Code Side Bot",
    version="1.0.0"
)

# Enable CORS for VS Code Webview connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MarkerRequest(BaseModel):
    filePath: str
    line: int


class DispatchRequest(BaseModel):
    agent: str  # "debug" or "test"
    filePath: str
    line: int
    column: Optional[int] = 1
    selectedCode: Optional[str] = ""
    surroundingCode: Optional[str] = ""
    language: Optional[str] = "plaintext"
    instruction: Optional[str] = ""
    source: Optional[str] = "supervisor"  # "developer" or "supervisor"


class FixRequest(BaseModel):
    filePath: str
    line: int
    originalCode: str
    suggestedFix: str
    userApproved: bool


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "supervisor": "active",
        "registered_models": ["debug", "test"],
        "has_ai_key": supervisor.engine.has_ai_credentials()
    }


@app.post("/api/marker")
def record_marker(req: MarkerRequest):
    supervisor.register_marker(req.filePath, req.line)
    return {"status": "ok", "message": f"Marker logged for {req.filePath}:{req.line}"}


@app.post("/api/task", response_model=AgentResult)
def execute_task(req: DispatchRequest):
    result = supervisor.dispatch_request(
        agent_type=req.agent,
        file_path=req.filePath,
        line=req.line,
        column=req.column or 1,
        selected_code=req.selectedCode or "",
        surrounding_code=req.surroundingCode or "",
        language=req.language or "plaintext",
        instruction=req.instruction or "",
        source=req.source or "supervisor"
    )
    return result


@app.get("/api/events")
def get_events():
    return {"events": supervisor.get_event_history()}


@app.get("/api/results")
def get_results():
    return {"results": supervisor.get_all_results()}


@app.post("/api/clear")
def clear_history():
    supervisor.clear_history()
    return {"status": "ok", "message": "History cleared"}


@app.post("/api/apply-fix")
def apply_fix(req: FixRequest):
    if not req.userApproved:
        raise HTTPException(status_code=403, detail="Permission required: developer did not approve code fix.")

    if not os.path.exists(req.filePath):
        raise HTTPException(status_code=404, detail=f"File not found: {req.filePath}")

    try:
        with open(req.filePath, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines(keepends=True)
        idx = req.line - 1
        if 0 <= idx < len(lines):
            lines[idx] = req.suggestedFix + ("\n" if not req.suggestedFix.endswith("\n") else "")
            new_content = "".join(lines)
            with open(req.filePath, "w", encoding="utf-8") as f:
                f.write(new_content)

            supervisor.event_log.record(
                event_type="fix_applied",
                message=f"Applied fix to {os.path.basename(req.filePath)}:{req.line} (developer approved)",
                file_path=req.filePath,
                line=req.line,
                status="success"
            )
            return {"status": "success", "message": f"Fix applied at line {req.line}"}
        else:
            raise HTTPException(status_code=400, detail="Target line is out of document bounds.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modify file: {str(e)}")


def create_server():
    return app
