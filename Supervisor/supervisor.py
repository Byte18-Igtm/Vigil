from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, cast

from adapters.debug_agent import StubDebugAgent
from adapters.test_agent import StubTestAgent
from adapters.understanding import StubUnderstanding
from adapters.nancy_agents import NancyDebugAdapter, NancyTestAdapter
from aggregation import aggregate, patch_hash
from explanation import build_explanation
from models import (
    ApprovalDecision,
    SubAgentInput,
    SubAgentResult,
    SupervisorReport,
)
from patching import PatchingError, apply_and_commit, check_repo, restore_branch, run_tests
from redaction import redact
from state import (
    ApprovalStateError,
    ConsentRequiredError,
    IllegalTransitionError,
    PatchHashMismatchError,
    Session,
    SessionState,
    SessionStore,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level state (reset with reset_for_tests())
# ---------------------------------------------------------------------------

_store = SessionStore()

_AGENT_MODE: str = os.environ.get("PATCHPERMIT_AGENT_MODE", "stub")

# Per-repo locks: keyed by os.path.realpath(repo_path), created lazily in async code
_repo_locks: Dict[str, asyncio.Lock] = {}


def _get_repo_lock(repo_path: str) -> asyncio.Lock:
    key = os.path.realpath(repo_path)
    if key not in _repo_locks:
        _repo_locks[key] = asyncio.Lock()
    return _repo_locks[key]

def _build_agents() -> Dict[str, Any]:
    """Return the agent dict appropriate for the current PATCHPERMIT_AGENT_MODE."""
    mode = os.environ.get("PATCHPERMIT_AGENT_MODE", "stub")
    if mode == "real":
        return {
            "debug": NancyDebugAdapter(),
            "test": NancyTestAdapter(),
        }
    return {
        "debug": StubDebugAgent(),
        "test": StubTestAgent(),
    }


def _mode_label() -> str:
    """Build the limitation/health label from the classes actually in _agents."""
    names = ", ".join(type(a).__name__ for a in _agents.values())
    return f"Agent mode: {_AGENT_MODE} ({names})"


_agents: Dict[str, Any] = _build_agents()
_understanding = StubUnderstanding()
_agent_timeout: float = float(os.environ.get("PATCHPERMIT_AGENT_TIMEOUT_SEC", "30"))


def configure(
    agents: Optional[Dict[str, Any]] = None,
    understanding: Optional[Any] = None,
    agent_timeout: Optional[float] = None,
) -> None:
    """Override agents, understanding provider, or timeout. Used in tests."""
    global _agents, _understanding, _agent_timeout
    if agents is not None:
        _agents = agents
    if understanding is not None:
        _understanding = understanding
    if agent_timeout is not None:
        _agent_timeout = agent_timeout


def reset_for_tests() -> None:
    """Reset all module-level state to defaults. Call in test teardown."""
    global _store, _agents, _understanding, _agent_timeout, _AGENT_MODE, _repo_locks
    _store = SessionStore()
    _AGENT_MODE = os.environ.get("PATCHPERMIT_AGENT_MODE", "stub")
    _agents = _build_agents()
    _understanding = StubUnderstanding()
    _agent_timeout = float(os.environ.get("PATCHPERMIT_AGENT_TIMEOUT_SEC", "30"))
    _repo_locks = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_transition(session_id: str, from_state: str, to_state: str) -> None:
    logger.info("[%s] %s → %s", session_id, from_state, to_state)


def _transition(session: Session, to_state: SessionState) -> None:
    from_state = session.state
    session.transition(to_state)
    _log_transition(session.session_id, from_state.value, to_state.value)


def _failed_report(session: Session, reason: str) -> SupervisorReport:
    """Build a minimal FAILED report and store it on the session."""
    report = SupervisorReport(
        session_id=session.session_id,
        state=SessionState.FAILED.value,
        explanation=redact(reason),
        root_cause="",
        patch=None,
        patch_hash=None,
        evidence=[],
        agent_statuses=[],
        conflicts=[],
        confidence=0.0,
        limitations=[],
        patch_source_agents=[],
        selection_reason=None,
        failure_reason=redact(reason),
        branch=None,
        test_result=None,
    )
    session.report = report
    return report


async def _run_agent(
    name: str,
    agent: Any,
    inp: SubAgentInput,
    timeout: float,
) -> SubAgentResult:
    """
    Run one agent with a timeout. Returns a SubAgentResult regardless of outcome.
    Timeout → status "timeout". Exception → status "failed" (error redacted).
    """
    try:
        result = await asyncio.wait_for(agent.run(inp), timeout=timeout)
        logger.info("[%s] agent %s: %s", inp.session_id, name, result.status)
        return result
    except asyncio.TimeoutError:
        logger.warning("[%s] agent %s timed out", inp.session_id, name)
        now = datetime.now(timezone.utc)
        _agent_lit = cast(Any, name)
        return SubAgentResult(
            agent=_agent_lit,
            status="timeout",
            summary=f"{name} timed out after {timeout}s",
            findings=[],
            proposed_patch=None,
            evidence=[],
            error=f"Timed out after {timeout}s",
            started_at=now,
            finished_at=now,
        )
    except Exception as exc:
        logger.error("[%s] agent %s raised %s", inp.session_id, name, type(exc).__name__)
        now = datetime.now(timezone.utc)
        error_msg = redact(f"{type(exc).__name__}: {exc}")
        _agent_lit = cast(Any, name)
        return SubAgentResult(
            agent=_agent_lit,
            status="failed",
            summary=f"{name} failed: {type(exc).__name__}",
            findings=[],
            proposed_patch=None,
            evidence=[],
            error=error_msg,
            started_at=now,
            finished_at=now,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def create_session(
    repo_path: str,
    bug_report: str,
    consent_confirmed: bool,
) -> str:
    """
    Create a new session. Returns the session_id.
    Raises ConsentRequiredError if consent_confirmed is False.
    Raises ValueError if repo_path does not exist.
    """
    if not consent_confirmed:
        raise ConsentRequiredError(
            "User consent is required before starting an investigation."
        )
    import os as _os
    if not _os.path.exists(repo_path):
        raise ValueError(f"repo_path does not exist: {repo_path!r}")

    session_id = uuid.uuid4().hex
    session = Session(
        session_id=session_id,
        repo_path=repo_path,
        bug_report=bug_report,
        consent_confirmed=True,
    )
    _store.create(session)
    logger.info("[%s] session created for repo %s", session_id, repo_path)
    return session_id


async def run_investigation(session_id: str) -> SupervisorReport:
    """
    Run the full investigation pipeline:
    CREATED → UNDERSTANDING → INVESTIGATING → AGGREGATING
           → AWAITING_APPROVAL | NO_PATCH | FAILED
    """
    session = _store.get(session_id)

    try:
        # --- UNDERSTANDING ---
        _transition(session, SessionState.UNDERSTANDING)
        try:
            understanding_summary = await _understanding.summarise(
                session.repo_path, session.bug_report
            )
        except Exception as exc:
            understanding_summary = f"Understanding unavailable: {type(exc).__name__}"
            logger.warning("[%s] understanding stub failed: %s", session_id, type(exc).__name__)

        # --- check repo (blocking git call) ---
        try:
            await asyncio.to_thread(check_repo, session.repo_path)
        except PatchingError as exc:
            _transition(session, SessionState.FAILED)
            return _failed_report(session, str(exc))

        # --- INVESTIGATING ---
        _transition(session, SessionState.INVESTIGATING)
        inp = SubAgentInput(
            session_id=session_id,
            repo_path=session.repo_path,
            bug_report=session.bug_report,
            understanding_summary=understanding_summary,
        )

        agent_tasks = {
            name: _run_agent(name, agent, inp, _agent_timeout)
            for name, agent in _agents.items()
        }
        results: List[SubAgentResult] = list(
            await asyncio.gather(*agent_tasks.values())
        )

        # --- AGGREGATING ---
        _transition(session, SessionState.AGGREGATING)

        def _apply_check_fn(patch: str) -> bool:
            import subprocess as sp
            try:
                r = sp.run(
                    ["git", "apply", "--check", "-"],
                    cwd=session.repo_path,
                    input=patch,
                    capture_output=True,
                    text=True,
                    shell=False,
                    timeout=15,
                )
                return r.returncode == 0
            except Exception:
                return False

        outcome = aggregate(results, _apply_check_fn)

        # Build report skeleton
        agent_statuses = outcome.agent_statuses
        mode_label = _mode_label()

        # Build location from highest-confidence finding of the chosen agent(s)
        location = None
        if outcome.chosen_patch and outcome.agent_statuses:
            from aggregation import _max_confidence as _mc
            best_finding = None
            for result in results:
                if result.agent in outcome.patch_source_agents and result.status == "ok":
                    for f in result.findings:
                        if best_finding is None or f.confidence > best_finding.confidence:
                            best_finding = f
            if best_finding is not None:
                try:
                    from pathlib import Path as _Path
                    abs_file = _Path(session.repo_path) / best_finding.file
                    file_lines = abs_file.read_text(encoding="utf-8").splitlines()
                    code_line = file_lines[best_finding.line - 1] if best_finding.line else ""
                    # Build context: 6 lines before and 6 after the target line
                    target_0 = (best_finding.line or 1) - 1  # 0-based
                    ctx_start = max(0, target_0 - 6)
                    ctx_end = min(len(file_lines), target_0 + 7)
                    context = [
                        {
                            "line": ctx_start + i + 1,
                            "code": file_lines[ctx_start + i],
                            "target": (ctx_start + i) == target_0,
                        }
                        for i in range(ctx_end - ctx_start)
                    ]
                except Exception:
                    code_line = ""
                    context = []
                location = {
                    "file": best_finding.file,
                    "line": best_finding.line,
                    "code": code_line,
                    "context": context,
                }

        report = SupervisorReport(
            session_id=session_id,
            state="",  # filled below after transition
            explanation="",
            root_cause=outcome.root_cause,
            patch=outcome.chosen_patch,
            patch_hash=outcome.patch_hash,
            evidence=outcome.evidence,
            agent_statuses=agent_statuses,
            conflicts=outcome.conflicts,
            confidence=outcome.confidence,
            limitations=outcome.limitations + [mode_label],
            patch_source_agents=outcome.patch_source_agents,
            selection_reason=outcome.selection_reason,
            failure_reason=outcome.failure_reason,
            branch=None,
            test_result=None,
            location=location,
        )

        if outcome.terminal_reason == "failed":
            _transition(session, SessionState.FAILED)
        elif outcome.terminal_reason == "no_patch":
            _transition(session, SessionState.NO_PATCH)
        else:
            _transition(session, SessionState.AWAITING_APPROVAL)

        report.state = session.state.value
        report.explanation = build_explanation(report)
        session.report = report
        logger.info("[%s] investigation complete: %s", session_id, session.state.value)
        return report

    except IllegalTransitionError:
        raise
    except Exception as exc:
        reason = redact(f"Unexpected error: {type(exc).__name__}: {exc}")
        logger.error("[%s] investigation failed: %s", session_id, reason)
        try:
            _transition(session, SessionState.FAILED)
        except IllegalTransitionError:
            pass
        return _failed_report(session, reason)


async def submit_approval(decision: ApprovalDecision) -> SupervisorReport:
    """
    Process an approval or rejection decision.
    Check order: session exists → idempotent return → state → decision → hash.
    Approval triggers _apply_patch under the session lock.
    """
    session = _store.get(decision.session_id)

    async with session.get_lock():
        # Idempotent: if approve and already past AWAITING_APPROVAL with same hash
        _post_approval_states = {
            SessionState.APPROVED, SessionState.APPLYING,
            SessionState.TESTING, SessionState.COMPLETED,
            SessionState.TESTS_FAILED,
        }
        if (
            decision.decision == "approve"
            and session.state in _post_approval_states
            and session.approval is not None
            and session.approval.patch_hash == decision.patch_hash
        ):
            logger.info(
                "[%s] idempotent approve returned (state=%s)",
                decision.session_id, session.state.value,
            )
            assert session.report is not None
            return session.report

        # Reject-after-approve or approve-after-reject
        if session.state == SessionState.REJECTED:
            raise ApprovalStateError(
                f"Session {decision.session_id} is already REJECTED."
            )

        # State check
        if session.state != SessionState.AWAITING_APPROVAL:
            raise ApprovalStateError(
                f"Approval requires AWAITING_APPROVAL state, "
                f"got {session.state.value}."
            )

        # Hash check
        assert session.report is not None
        if decision.patch_hash != session.report.patch_hash:
            raise PatchHashMismatchError(
                "patch_hash in decision does not match the proposed patch."
            )

        session.approval = decision
        logger.info(
            "[%s] approval decision: %s", decision.session_id, decision.decision
        )

        if decision.decision == "reject":
            _transition(session, SessionState.REJECTED)
            session.report.state = SessionState.REJECTED.value
            return session.report

        # Approve: transition to APPROVED before any await
        _transition(session, SessionState.APPROVED)
        session.report.state = SessionState.APPROVED.value

    # Apply outside the lock to avoid blocking other sessions
    await _apply_patch(session)
    return session.report


async def _apply_patch(session: Session) -> None:
    """
    Private: apply the patch and run tests.
    Verifies state == APPROVED and hash matches before touching the repo.
    """
    # Runtime invariant check
    if session.state != SessionState.APPROVED:
        raise IllegalTransitionError(session.state, SessionState.APPLYING)
    assert session.approval is not None
    assert session.report is not None
    assert session.report.patch is not None

    live_hash = patch_hash(session.report.patch)
    if session.approval.patch_hash != live_hash:
        raise PatchHashMismatchError(
            "Patch hash mismatch at apply time — refusing to apply."
        )

    repo_lock = _get_repo_lock(session.repo_path)
    async with repo_lock:
        try:
            _transition(session, SessionState.APPLYING)
            session.report.state = SessionState.APPLYING.value

            start_branch, new_branch = await asyncio.to_thread(
                apply_and_commit,
                session.repo_path,
                session.report.patch,
                session.session_id,
            )
            session.report.branch = new_branch

            _transition(session, SessionState.TESTING)
            session.report.state = SessionState.TESTING.value

            test_result = await asyncio.to_thread(run_tests, session.repo_path)
            session.report.test_result = test_result

            if test_result.passed:
                _transition(session, SessionState.COMPLETED)
            else:
                _transition(session, SessionState.TESTS_FAILED)
                # Restore starting branch; patch branch kept for inspection
                try:
                    await asyncio.to_thread(restore_branch, session.repo_path, start_branch)
                except PatchingError as exc:
                    logger.warning(
                        "[%s] could not restore branch: %s",
                        session.session_id, str(exc),
                    )

            session.report.state = session.state.value
            logger.info(
                "[%s] apply complete: %s (branch=%s)",
                session.session_id, session.state.value, new_branch,
            )

        except PatchingError as exc:
            reason = redact(str(exc))
            logger.error("[%s] patching failed: %s", session.session_id, reason)
            try:
                _transition(session, SessionState.FAILED)
            except IllegalTransitionError:
                pass
            session.report.failure_reason = reason
            session.report.state = session.state.value


def get_session_report(session_id: str) -> SupervisorReport:
    """Return the current report for a session, or raise SessionNotFoundError."""
    session = _store.get(session_id)
    if session.report is None:
        # Session exists but investigation hasn't run yet
        return SupervisorReport(
            session_id=session_id,
            state=session.state.value,
            explanation="",
            root_cause="",
            patch=None,
            patch_hash=None,
            evidence=[],
            agent_statuses=[],
            conflicts=[],
            confidence=0.0,
            limitations=[],
            patch_source_agents=[],
            selection_reason=None,
            failure_reason=None,
            branch=None,
            test_result=None,
            location=None,
        )
    return session.report
