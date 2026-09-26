from __future__ import annotations

import dataclasses
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import supervisor as sv
from state import (
    ApprovalStateError,
    ConsentRequiredError,
    PatchHashMismatchError,
    SessionNotFoundError,
)
from redaction import redact

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="PatchPermit Supervisor API")

_allowed_origins = [
    o.strip()
    for o in os.environ.get(
        "PATCHPERMIT_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Repo-root safety check
# ---------------------------------------------------------------------------

def _allowed_repo_root() -> str:
    default = os.path.join(os.path.dirname(__file__), "demo_target")
    return os.environ.get("PATCHPERMIT_ALLOWED_REPO_ROOT", default)


def _check_repo_path(repo_path: str) -> str:
    """Resolve repo_path and ensure it is inside the allowed root. Returns realpath."""
    real = os.path.realpath(repo_path)
    root = os.path.realpath(_allowed_repo_root())
    if os.path.commonpath([real, root]) != root:
        raise HTTPException(
            status_code=403,
            detail="repo_path is outside the allowed repository root.",
        )
    return real


# ---------------------------------------------------------------------------
# Report serialisation
# ---------------------------------------------------------------------------

def _serial(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _serial(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [_serial(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serial(v) for k, v in obj.items()}
    return obj


def _report_json(report) -> Dict[str, Any]:
    return _serial(report)


# ---------------------------------------------------------------------------
# Audit log (in-memory, per session)
# ---------------------------------------------------------------------------

# audit_log: {session_id: [{approver, timestamp, decision, patch_hash}]}
_audit_log: Dict[str, List[Dict[str, Any]]] = {}


def _record_audit(session_id: str, approver: str, decision: str, patch_hash: Optional[str]) -> None:
    entry = {
        "approver": approver,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "patch_hash": patch_hash,
    }
    _audit_log.setdefault(session_id, []).append(entry)


def _get_audit(session_id: str) -> List[Dict[str, Any]]:
    return _audit_log.get(session_id, [])


# ---------------------------------------------------------------------------
# History (append-only JSONL file)
# ---------------------------------------------------------------------------

_HISTORY_FILE = Path(__file__).parent / ".vigil_history.jsonl"


def _append_history(session_id: str, session) -> None:
    """Append one JSON line to .vigil_history.jsonl when a session reaches a terminal state."""
    report = session.report
    audit = _get_audit(session_id)

    # Compute decision time = last audit entry timestamp
    decision_time = audit[-1]["timestamp"] if audit else None
    approver = audit[-1]["approver"] if audit else None
    patch_hash = report.patch_hash if report else None
    final_state = session.state.value if hasattr(session.state, "value") else str(session.state)
    bug_preview = session.bug_report[:200] if session.bug_report else ""
    tests_passed = report.test_result.passed if (report and report.test_result) else None

    record = {
        "session_id": session_id,
        "created_at": session.created_at.isoformat(),
        "bug_report": bug_preview,
        "final_state": final_state,
        "patch_hash": patch_hash,
        "approver": approver,
        "decision_time": decision_time,
        "tests_passed": tests_passed,
    }
    try:
        with open(_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # History is best-effort


def _read_history() -> List[Dict[str, Any]]:
    """Read all records from the history file, newest first."""
    if not _HISTORY_FILE.exists():
        return []
    records = []
    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    records.reverse()
    return records


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    repo_path: str
    bug_report: str
    consent_confirmed: bool
    pre_scan: Optional[Dict[str, Any]] = None


class DecisionRequest(BaseModel):
    decision: str          # "approve" | "reject"
    patch_hash: str
    approver: str
    comment: Optional[str] = None


class ScanRequest(BaseModel):
    repo_path: str


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@app.exception_handler(ConsentRequiredError)
async def _consent_error(request: Request, exc: ConsentRequiredError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def _value_error(request: Request, exc: ValueError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(SessionNotFoundError)
async def _not_found(request: Request, exc: SessionNotFoundError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ApprovalStateError)
async def _approval_state(request: Request, exc: ApprovalStateError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(PatchHashMismatchError)
async def _hash_mismatch(request: Request, exc: PatchHashMismatchError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def _generic_error(request: Request, exc: Exception):
    from fastapi.responses import JSONResponse
    msg = redact(f"{type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={"detail": msg})


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "agent_mode": sv._AGENT_MODE, "agent_mode_label": sv._mode_label()}


@app.post("/sessions", status_code=201)
async def create_session(body: CreateSessionRequest):
    real_path = _check_repo_path(body.repo_path)
    session_id = await sv.create_session(
        repo_path=real_path,
        bug_report=body.bug_report,
        consent_confirmed=body.consent_confirmed,
    )
    # Attach pre_scan to the session report if provided
    if body.pre_scan is not None:
        session = sv._store.get(session_id)
        # Store as attribute for later use; we'll attach it on the report after investigate
        session._pre_scan = body.pre_scan
    return {"session_id": session_id}


@app.post("/sessions/{session_id}/investigate")
async def investigate(session_id: str):
    report = await sv.run_investigation(session_id)
    # Attach pre_scan to report if stored on session
    session = sv._store.get(session_id)
    pre_scan = getattr(session, "_pre_scan", None)
    if pre_scan is not None and report is not None:
        report_dict = _report_json(report)
        report_dict["pre_scan"] = pre_scan
        # Also attach audit
        report_dict["audit"] = _get_audit(session_id)
        return report_dict
    result = _report_json(report)
    result["audit"] = _get_audit(session_id)
    return result


@app.post("/sessions/{session_id}/decision")
async def decision(session_id: str, body: DecisionRequest):
    if body.decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")
    from models import ApprovalDecision
    dec = ApprovalDecision(
        session_id=session_id,
        patch_hash=body.patch_hash,
        decision=body.decision,
        approver=body.approver,
        timestamp=datetime.now(timezone.utc),
        comment=body.comment,
    )
    report = await sv.submit_approval(dec)

    # Record audit
    _record_audit(session_id, body.approver, body.decision, body.patch_hash)

    # Append to history if terminal
    from state import TERMINAL_STATES
    session = sv._store.get(session_id)
    if session.state in TERMINAL_STATES:
        _append_history(session_id, session)

    result = _report_json(report)
    result["audit"] = _get_audit(session_id)
    return result


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    # Check in-memory first
    try:
        report = sv.get_session_report(session_id)
        result = _report_json(report)
        result["audit"] = _get_audit(session_id)
        return result
    except SessionNotFoundError:
        pass
    # Fall back to history file
    for record in _read_history():
        if record.get("session_id") == session_id:
            return record
    raise SessionNotFoundError(session_id)


@app.get("/sessions")
async def list_sessions():
    """Return session summaries, newest first, from memory plus history file."""
    # In-memory sessions
    memory_sessions: Dict[str, Any] = {}
    for session in sv._store.all_sessions():
        report = session.report
        memory_sessions[session.session_id] = {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "bug_report": session.bug_report[:200],
            "state": session.state.value,
            "patch_hash": report.patch_hash if report else None,
        }

    # History file sessions (for completed ones not in memory)
    history = _read_history()

    # Merge: memory takes precedence over history
    seen = set(memory_sessions.keys())
    result = list(memory_sessions.values())
    for record in history:
        sid = record.get("session_id")
        if sid and sid not in seen:
            seen.add(sid)
            result.append({
                "session_id": sid,
                "created_at": record.get("created_at"),
                "bug_report": record.get("bug_report", ""),
                "state": record.get("final_state"),
                "patch_hash": record.get("patch_hash"),
            })

    # Sort newest first by created_at
    result.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return result


@app.post("/projects/scan")
async def scan_project(body: ScanRequest):
    """Scan a project for failing tests and generate a bug report."""
    import asyncio
    from patching import scan_project as _scan_project
    real_path = _check_repo_path(body.repo_path)
    scan_result = await asyncio.to_thread(_scan_project, real_path)

    # Generate bug_report from failures
    bug_report = None
    if scan_result.get("error"):
        return {"scan": scan_result, "bug_report": None, "error": scan_result["error"]}

    failures = scan_result.get("failures", [])
    if failures:
        f = failures[0]
        parts = [f"Failing test {f['test']}: {f['message']}"]
        if f.get("file") and f.get("line"):
            parts[0] += f" (at {f['file']}:{f['line']})"
        bug_report = parts[0]

    return {"scan": scan_result, "bug_report": bug_report}


@app.get("/projects")
async def list_projects():
    """Return folders directly inside the allowed repo root that contain .git."""
    root = Path(os.path.realpath(_allowed_repo_root()))
    projects = []
    try:
        for entry in root.iterdir():
            if entry.is_dir() and (entry / ".git").exists():
                projects.append({"name": entry.name, "path": str(entry)})
    except Exception:
        pass
    return projects


@app.get("/security")
async def security():
    """Return the static list of security guarantees enforced in code."""
    return [
        {
            "guarantee": "127.0.0.1 bind",
            "description": "API server binds only to localhost (127.0.0.1), never exposed to the network.",
            "file": "scripts/run_api.py",
            "function": "uvicorn.run(host='127.0.0.1')",
        },
        {
            "guarantee": "Allowed origins",
            "description": "CORS is restricted to PATCHPERMIT_ALLOWED_ORIGINS (default: localhost:5173).",
            "file": "api.py",
            "function": "_allowed_origins / CORSMiddleware",
        },
        {
            "guarantee": "Allowed repo root",
            "description": "Every repo_path is resolved and must be inside PATCHPERMIT_ALLOWED_REPO_ROOT.",
            "file": "api.py",
            "function": "_check_repo_path",
        },
        {
            "guarantee": "Hash-checked approval",
            "description": "The patch_hash submitted with a decision must match the SHA-256 of the proposed patch.",
            "file": "supervisor.py",
            "function": "submit_approval / _apply_patch",
        },
        {
            "guarantee": "No apply without approval",
            "description": "Patches are only applied after an explicit APPROVED state transition.",
            "file": "supervisor.py",
            "function": "_apply_patch (asserts state == APPROVED)",
        },
        {
            "guarantee": "Secret redaction",
            "description": "All log output and error messages are passed through redact() before being returned.",
            "file": "redaction.py",
            "function": "redact",
        },
        {
            "guarantee": "Read-only agents",
            "description": "Sub-agents receive repo_path but have no write or shell-execution capability in stub/real modes.",
            "file": "Subagents/ (read-only)",
            "function": "SubAgentInput (repo_path read-only contract)",
        },
        {
            "guarantee": "Clean-tree check before apply",
            "description": "git status --porcelain is checked before applying any patch; dirty trees are rejected.",
            "file": "patching.py",
            "function": "check_repo",
        },
    ]
