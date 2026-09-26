from __future__ import annotations

import pytest

from state import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    Session,
    SessionState,
    IllegalTransitionError,
    SessionStore,
    SessionNotFoundError,
)


# ---------------------------------------------------------------------------
# Ground-truth transition table (written out literally; not imported)
# ---------------------------------------------------------------------------

EXPECTED_TRANSITIONS: dict = {
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
    SessionState.COMPLETED:         frozenset(),
    SessionState.TESTS_FAILED:      frozenset(),
    SessionState.REJECTED:          frozenset(),
    SessionState.NO_PATCH:          frozenset(),
    SessionState.FAILED:            frozenset(),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_session(state: SessionState = SessionState.CREATED) -> Session:
    s = Session(
        session_id="test-001",
        repo_path="/fake/repo",
        bug_report="bug",
        consent_confirmed=True,
    )
    s.state = state
    return s


def _all_illegal_pairs():
    """Yield pytest.param for every (from, to) pair not in EXPECTED_TRANSITIONS."""
    all_states = sorted(SessionState, key=lambda s: s.value)
    for from_s in all_states:
        allowed = EXPECTED_TRANSITIONS.get(from_s, frozenset())
        for to_s in all_states:
            if to_s not in allowed:
                yield pytest.param(
                    from_s, to_s,
                    id=f"{from_s.value}->{to_s.value}",
                )


# ---------------------------------------------------------------------------
# Transition table integrity
# ---------------------------------------------------------------------------

class TestTransitionTable:
    def test_allowed_transitions_matches_expected(self):
        assert ALLOWED_TRANSITIONS == EXPECTED_TRANSITIONS

    def test_applying_only_reachable_from_approved(self):
        # Checked against ALLOWED_TRANSITIONS (the real table), not EXPECTED_TRANSITIONS
        reachable_from = sorted(
            [s.value for s, targets in ALLOWED_TRANSITIONS.items()
             if SessionState.APPLYING in targets]
        )
        assert reachable_from == [SessionState.APPROVED.value]


# ---------------------------------------------------------------------------
# Every illegal (from, to) pair raises IllegalTransitionError
# ---------------------------------------------------------------------------

class TestIllegalTransitions:
    @pytest.mark.parametrize("from_s,to_s", list(_all_illegal_pairs()))
    def test_illegal_pair_raises(self, from_s, to_s):
        s = make_session(from_s)
        with pytest.raises(IllegalTransitionError) as exc_info:
            s.transition(to_s)
        assert exc_info.value.from_state == from_s
        assert exc_info.value.to_state == to_s


# ---------------------------------------------------------------------------
# Every non-terminal state can transition to FAILED
# ---------------------------------------------------------------------------

NON_TERMINAL_STATES_SORTED = sorted(
    (s for s in SessionState if s not in TERMINAL_STATES),
    key=lambda s: s.value,
)


class TestFailedEscape:
    @pytest.mark.parametrize(
        "state",
        NON_TERMINAL_STATES_SORTED,
        ids=[s.value for s in NON_TERMINAL_STATES_SORTED],
    )
    def test_any_non_terminal_can_go_to_failed(self, state):
        s = make_session(state)
        s.transition(SessionState.FAILED)
        assert s.state == SessionState.FAILED


# ---------------------------------------------------------------------------
# SessionStore
# ---------------------------------------------------------------------------

class TestSessionStore:
    def test_get_unknown_raises(self):
        store = SessionStore()
        with pytest.raises(SessionNotFoundError):
            store.get("no-such-id")

    def test_create_duplicate_raises(self):
        store = SessionStore()
        s = make_session()
        store.create(s)
        with pytest.raises(ValueError, match="already exists"):
            store.create(s)

    def test_get_returns_stored_session(self):
        store = SessionStore()
        s = make_session()
        store.create(s)
        assert store.get("test-001") is s
