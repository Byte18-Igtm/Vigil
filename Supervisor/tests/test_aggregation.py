from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import pytest

from aggregation import (
    _changed_old_lines,
    aggregate,
    patch_hash,
)
from models import (
    EvidenceItem,
    Finding,
    SubAgentResult,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)
_ALWAYS_OK = lambda _p: True   # noqa: E731
_ALWAYS_FAIL = lambda _p: False  # noqa: E731


def _result(
    agent: str,
    status: str = "ok",
    patch: Optional[str] = None,
    findings: Optional[List[Finding]] = None,
    evidence: Optional[List[EvidenceItem]] = None,
    error: Optional[str] = None,
) -> SubAgentResult:
    return SubAgentResult(
        agent=agent,
        status=status,
        summary=f"{agent} summary",
        findings=findings or [],
        proposed_patch=patch,
        evidence=evidence or [],
        error=error,
        started_at=_NOW,
        finished_at=_NOW,
    )


# ---------------------------------------------------------------------------
# Fixtures: realistic unified diffs with matching hunk counts
#
# File contents assumed:
#   calc.py:
#     line 1: def average(numbers):
#     line 2:     return sum(numbers) // len(numbers)
#   utils.py:
#     line 1: x = 1
#
# "@@ -1,2 +1,2 @@": old starts at line 1, 2 old lines shown (1 context + 1 removed)
#                     new starts at line 1, 2 new lines shown (1 context + 1 added)
# ---------------------------------------------------------------------------

# Fixes line 2: changes // → /
_PATCH_CALC_FIX = (
    "--- a/calc.py\n"
    "+++ b/calc.py\n"
    "@@ -1,2 +1,2 @@\n"
    " def average(numbers):\n"
    "-    return sum(numbers) // len(numbers)\n"
    "+    return sum(numbers) / len(numbers)\n"
)

# Renames function on line 1; line 2 kept as context
_PATCH_CALC_RENAME = (
    "--- a/calc.py\n"
    "+++ b/calc.py\n"
    "@@ -1,2 +1,2 @@\n"
    "-def average(numbers):\n"
    "+def mean(numbers):\n"
    "     return sum(numbers) // len(numbers)\n"
)

# Touches a completely different file
_PATCH_OTHER_FILE = (
    "--- a/utils.py\n"
    "+++ b/utils.py\n"
    "@@ -1,1 +1,1 @@\n"
    "-x = 1\n"
    "+x = 2\n"
)

# Findings
_FINDING_CALC_LINE2 = Finding(
    file="calc.py", claim="floor division bug",
    confidence=0.7, evidence_ids=["ev-1"], line=2,
)
_FINDING_CALC_LINE1 = Finding(
    file="calc.py", claim="wrong function name",
    confidence=0.9, evidence_ids=["ev-2"], line=1,
)
_FINDING_CALC_NO_LINE = Finding(
    file="calc.py", claim="floor division bug",
    confidence=0.7, evidence_ids=["ev-1"], line=None,
)

# Evidence
_EVIDENCE_DEBUG = [EvidenceItem(id="ev-1", type="code_ref",    source="debug",       content="line 2")]
_EVIDENCE_TEST  = [EvidenceItem(id="ev-1", type="test_output", source="test",        content="fail")]
_EVIDENCE_MAINT = [EvidenceItem(id="ev-2", type="reasoning",   source="maintenance", content="rename")]


# ---------------------------------------------------------------------------
# _changed_old_lines unit tests
# ---------------------------------------------------------------------------

class TestChangedOldLines:
    def test_context_lines_excluded(self):
        # @@ -1,2: old starts at line 1.
        # Line 1 is context (advances counter, not recorded).
        # Line 2 is removed (recorded).
        result = _changed_old_lines(_PATCH_CALC_FIX)
        assert result == {"calc.py": {2}}

    def test_rename_patch_removes_line_1(self):
        # @@ -1,2: line 1 is removed, line 2 is context.
        result = _changed_old_lines(_PATCH_CALC_RENAME)
        assert result == {"calc.py": {1}}

    def test_multi_hunk(self):
        multi = (
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -1,3 +1,3 @@\n"
            " context\n"
            "-removed_line_2\n"
            "+added\n"
            " context\n"
            "@@ -10,3 +10,3 @@\n"
            " context\n"
            "-removed_line_11\n"
            "+added\n"
            " context\n"
        )
        result = _changed_old_lines(multi)
        assert result == {"foo.py": {2, 11}}

    def test_pure_insertion_records_insertion_point(self):
        # @@ -5,2: old starts at line 5.
        # First line is context → old_lineno advances to 6.
        # Then '+' inserts BEFORE old line 6 → insertion_point = 6.
        insert_patch = (
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -5,2 +5,3 @@\n"
            " context\n"
            "+new line\n"
            " context\n"
        )
        result = _changed_old_lines(insert_patch)
        assert result == {"foo.py": {6}}

    def test_no_newline_marker_does_not_advance_counter(self):
        patch_with_marker = (
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-old line\n"
            "\\ No newline at end of file\n"
            "+new line\n"
        )
        result = _changed_old_lines(patch_with_marker)
        # The '\ No newline' marker must not advance the counter;
        # only line 1 is removed.
        assert result == {"foo.py": {1}}


# ---------------------------------------------------------------------------
# Core aggregation tests
# ---------------------------------------------------------------------------

class TestAllAgentsOk:
    def test_single_patch_chosen_evidence_prefixed(self):
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2], evidence=_EVIDENCE_DEBUG)
        outcome = aggregate([debug], _ALWAYS_OK)
        assert outcome.terminal_reason is None
        assert outcome.chosen_patch == _PATCH_CALC_FIX
        assert outcome.patch_hash == patch_hash(_PATCH_CALC_FIX)
        assert outcome.patch_source_agents == ["debug"]
        assert all(e.id.startswith("debug:") for e in outcome.evidence)
        assert all(e.source == "debug" for e in outcome.evidence)


class TestDemoScenario:
    """
    calc.py line 1 = def, line 2 = return //.
    Debug:       fix patch (line 2), confidence 0.7.
    Maintenance: rename patch (line 1), confidence 0.9 (higher than debug).
    Test:        no patch, finding on calc.py line 2.

    Test agent finding (line 2) falls within debug's changed lines ({2}),
    but NOT within maintenance's changed lines ({1}).
    → debug is corroborated; maintenance is not.
    → debug wins despite lower confidence.
    → maintenance → conflict with resolution "picked_debug".
    → selection_reason contains "test (finding on calc.py:2)".
    """

    def _make_results(self):
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2], evidence=_EVIDENCE_DEBUG)
        maintenance = _result("maintenance", patch=_PATCH_CALC_RENAME,
                               findings=[_FINDING_CALC_LINE1], evidence=_EVIDENCE_MAINT)
        test = _result("test", patch=None,
                       findings=[_FINDING_CALC_LINE2], evidence=_EVIDENCE_TEST)
        return [debug, maintenance, test]

    def test_debug_chosen_maintenance_conflict(self):
        outcome = aggregate(self._make_results(), _ALWAYS_OK)
        assert outcome.chosen_patch == _PATCH_CALC_FIX
        assert outcome.patch_source_agents == ["debug"]
        picked_resolutions = [
            c.resolution for c in outcome.conflicts
            if "maintenance" in c.agents_involved and c.resolution.startswith("picked_")
        ]
        assert picked_resolutions == ["picked_debug"]

    def test_selection_reason_names_test_agent(self):
        outcome = aggregate(self._make_results(), _ALWAYS_OK)
        assert outcome.selection_reason is not None
        assert "test (finding on calc.py:2)" in outcome.selection_reason

    def test_no_line_falls_through_to_confidence(self):
        """
        finding.line=None → test agent corroborates BOTH debug (line 2) and
        maintenance (line 1). Both are corroborated. Next tiebreak: confidence.
        Maintenance has 0.9 > debug's 0.7, so maintenance wins.
        Documents the confidence-fallback behaviour when line-level filtering
        does not distinguish candidates.
        """
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2])
        maintenance = _result("maintenance", patch=_PATCH_CALC_RENAME,
                               findings=[_FINDING_CALC_LINE1])
        test = _result("test", patch=None, findings=[_FINDING_CALC_NO_LINE])
        outcome = aggregate([debug, maintenance, test], _ALWAYS_OK)
        assert outcome.chosen_patch == _PATCH_CALC_RENAME

    def test_failed_agent_does_not_corroborate(self):
        """
        Test agent with status='failed' must not appear in selection_reason.
        With no corroboration, confidence decides: maintenance (0.9) beats
        debug (0.7). Key assertion: 'test' is absent from selection_reason.
        """
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2])
        maintenance = _result("maintenance", patch=_PATCH_CALC_RENAME,
                               findings=[_FINDING_CALC_LINE1])
        test_failed = _result("test", status="failed",
                               findings=[_FINDING_CALC_LINE2])
        outcome = aggregate([debug, maintenance, test_failed], _ALWAYS_OK)
        assert outcome.selection_reason is not None
        assert "test" not in outcome.selection_reason


class TestAgentStatuses:
    def test_timeout_and_failed_recorded(self):
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2])
        timeout_r = _result("test", status="timeout", error="timed out")
        failed_r = _result("maintenance", status="failed", error="crashed")
        outcome = aggregate([debug, timeout_r, failed_r], _ALWAYS_OK)
        assert outcome.terminal_reason is None
        statuses = {e.agent: e.status for e in outcome.agent_statuses}
        assert statuses["test"] == "timeout"
        assert statuses["maintenance"] == "failed"
        assert statuses["debug"] == "ok"


class TestTerminalOutcomes:
    def test_all_failed_returns_failed(self):
        r1 = _result("debug", status="failed", error="err")
        r2 = _result("test", status="timeout", error="timeout")
        r3 = _result("maintenance", status="skipped")
        outcome = aggregate([r1, r2, r3], _ALWAYS_OK)
        assert outcome.terminal_reason == "failed"
        assert outcome.failure_reason is not None

    def test_ok_agents_no_patches_returns_no_patch(self):
        r1 = _result("debug", patch=None, findings=[_FINDING_CALC_LINE2])
        r2 = _result("test", patch=None)
        outcome = aggregate([r1, r2], _ALWAYS_OK)
        assert outcome.terminal_reason == "no_patch"


class TestApplyCheck:
    def test_failing_check_drops_patch_adds_limitation(self):
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2])
        maint = _result("maintenance", patch=_PATCH_OTHER_FILE,
                        findings=[Finding("utils.py", "wrong value", 0.5, [], None)])
        # Only _PATCH_OTHER_FILE passes
        outcome = aggregate([debug, maint], lambda p: p == _PATCH_OTHER_FILE)
        assert outcome.chosen_patch == _PATCH_OTHER_FILE
        assert any("debug" in lim for lim in outcome.limitations)

    def test_apply_check_exception_treated_as_failure(self):
        def boom(_p: str) -> bool:
            raise RuntimeError("secret path /home/user/.ssh/id_rsa")

        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2])
        outcome = aggregate([debug], boom)
        assert outcome.terminal_reason == "no_patch"
        assert any("RuntimeError" in lim for lim in outcome.limitations)
        assert not any("secret" in lim for lim in outcome.limitations)
        assert not any("id_rsa" in lim for lim in outcome.limitations)


class TestDeduplication:
    def test_identical_patches_deduped_as_corroboration(self):
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2])
        test = _result("test", patch=_PATCH_CALC_FIX,
                       findings=[_FINDING_CALC_LINE2])
        outcome = aggregate([debug, test], _ALWAYS_OK)
        assert outcome.terminal_reason is None
        assert set(outcome.patch_source_agents) == {"debug", "test"}
        # Only one candidate → no "picked_" conflict
        assert not any(c.resolution.startswith("picked_") for c in outcome.conflicts)
        # selection_reason must mention "identical patch"
        assert outcome.selection_reason is not None
        assert "identical patch" in outcome.selection_reason


class TestNonOverlappingAlternative:
    def test_non_overlapping_in_limitations_not_picked_conflict(self):
        """
        Debug patch (calc.py) is chosen. Maintenance patch (utils.py) is
        non-overlapping → goes to limitations, not a "picked_" conflict.
        The primary-file rule (step 7) legitimately adds one "open" conflict
        because debug's primary file is calc.py and maintenance's is utils.py.
        """
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2])
        maint = _result("maintenance", patch=_PATCH_OTHER_FILE,
                        findings=[Finding("utils.py", "wrong value", 0.5, [], None)])
        outcome = aggregate([debug, maint], _ALWAYS_OK)
        # No "picked_" conflict involving maintenance
        assert not any(
            "maintenance" in c.agents_involved and c.resolution.startswith("picked_")
            for c in outcome.conflicts
        )
        # Maintenance IS in limitations
        assert any("maintenance" in lim for lim in outcome.limitations)
        # Exactly one "open" conflict from the primary-file disagreement
        open_conflicts = [c for c in outcome.conflicts if c.resolution == "open"]
        assert len(open_conflicts) == 1


class TestDeterminism:
    def _make_results(self):
        debug = _result("debug", patch=_PATCH_CALC_FIX,
                        findings=[_FINDING_CALC_LINE2], evidence=_EVIDENCE_DEBUG)
        maintenance = _result("maintenance", patch=_PATCH_CALC_RENAME,
                               findings=[_FINDING_CALC_LINE1], evidence=_EVIDENCE_MAINT)
        test = _result("test", patch=None,
                       findings=[_FINDING_CALC_LINE2], evidence=_EVIDENCE_TEST)
        return debug, maintenance, test

    def test_shuffled_input_same_result(self):
        debug, maintenance, test = self._make_results()
        o1 = aggregate([debug, maintenance, test], _ALWAYS_OK)
        o2 = aggregate([maintenance, test, debug], _ALWAYS_OK)
        o3 = aggregate([test, debug, maintenance], _ALWAYS_OK)
        assert o1.chosen_patch == o2.chosen_patch == o3.chosen_patch
        assert o1.selection_reason == o2.selection_reason == o3.selection_reason
        assert (
            [c.resolution for c in o1.conflicts] ==
            [c.resolution for c in o2.conflicts] ==
            [c.resolution for c in o3.conflicts]
        )
        assert (
            [c.agents_involved for c in o1.conflicts] ==
            [c.agents_involved for c in o2.conflicts] ==
            [c.agents_involved for c in o3.conflicts]
        )
