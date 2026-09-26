from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, FrozenSet, List, Optional

from models import ApprovalDecision, SupervisorReport


class SessionState(str, Enum):
    CREATED           = "CREATED"
    UNDERSTANDING     = "UNDERSTANDING"
    INVESTIGATING     = "INVESTIGATING"
    AGGREGATING       = "AGGREGATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    NO_PATCH          = "NO_PATCH"
    APPROVED          = "APPROVED"
    REJECTED          = "REJECTED"
    APPLYING          = "APPLYING"
    TESTING           = "TESTING"
    COMPLETED         = "COMPLETED"
    TESTS_FAILED      = "TESTS_FAILED"
    FAILED            = "FAILED"


TERMINAL_STATES: FrozenSet[SessionState] = frozenset({
    SessionState.COMPLETED,
    SessionState.TESTS_FAILED,
    SessionState.REJECTED,
    SessionState.NO_PATCH,
    SessionState.FAILED,
})

ALLOWED_TRANSITIONS: Dict[SessionState, FrozenSet[SessionState]] = {
    SessionState.CREATED:           frozenset({SessionState.UNDERSTANDING,
                                               SessionState.FAILED}),
    SessionState.UNDERSTANDING:     frozenset({SessionState.INVESTIGATING,
                                               SessionState.FAILED}),
    SessionState.INVESTIGATING:     frozenset({SessionState.AGGREGATING,
                                               SessionState.FAILED}),
    SessionState.AGGREGATING:       frozenset({SessionState.AWAITING_APPROVAL,
                                               SessionState.NO_PATCH,
                                               SessionState.FAILED}),
    SessionState.AWAITING_APPROVAL: frozenset({SessionState.APPROVED,
                                               SessionState.REJECTED,
                                               SessionState.FAILED}),
    SessionState.APPROVED:          frozenset({SessionState.APPLYING,
                                               SessionState.FAILED}),
    SessionState.APPLYING:          frozenset({SessionState.TESTING,
                                               SessionState.FAILED}),
    SessionState.TESTING:           frozenset({SessionState.COMPLETED,
                                               SessionState.TESTS_FAILED,
                                               SessionState.FAILED}),
    # Terminal states: no outgoing edges
    SessionState.COMPLETED:         frozenset(),
    SessionState.TESTS_FAILED:      frozenset(),
    SessionState.REJECTED:          frozenset(),
    SessionState.NO_PATCH:          frozenset(),
    SessionState.FAILED:            frozenset(),
}


# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------

class PatchPermitError(Exception):
    """Base for all PatchPermit errors."""

class IllegalTransitionError(PatchPermitError):
    def __init__(self, from_state: SessionState, to_state: SessionState) -> None:
        super().__init__(
            f"Transition {from_state.value} -> {to_state.value} is not allowed"
        )
        self.from_state = from_state
        self.to_state = to_state

class ConsentRequiredError(PatchPermitError):
    pass

class SessionNotFoundError(PatchPermitError):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session not found: {session_id}")
        self.session_id = session_id

class ApprovalStateError(PatchPermitError):
    pass

class PatchHashMismatchError(PatchPermitError):
    pass


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@dataclass
class Session:
    session_id: str
    repo_path: str
    bug_report: str
    consent_confirmed: bool
    state: SessionState = SessionState.CREATED
    report: Optional[SupervisorReport] = None
    approval: Optional[ApprovalDecision] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    # Lock is created lazily inside async context to avoid cross-loop issues on 3.9
    _lock: Optional[asyncio.Lock] = field(default=None, repr=False, compare=False)

    def get_lock(self) -> asyncio.Lock:
        """Return (creating if needed) the per-session asyncio.Lock.
        Must only be called from within a running event loop."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def transition(self, to_state: SessionState) -> None:
        """Enforce the transition table. Raises IllegalTransitionError on violation."""
        allowed = ALLOWED_TRANSITIONS.get(self.state, frozenset())
        if to_state not in allowed:
            raise IllegalTransitionError(self.state, to_state)
        self.state = to_state


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create(self, session: Session) -> None:
        if session.session_id in self._sessions:
            raise ValueError(
                f"Session already exists: {session.session_id}"
            )
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> Session:
        try:
            return self._sessions[session_id]
        except KeyError:
            raise SessionNotFoundError(session_id) from None

    def all_sessions(self) -> List[Session]:
        return list(self._sessions.values())
