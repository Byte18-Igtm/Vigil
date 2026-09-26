from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from adapters.debug_agent import STUB_DEBUG_PATCH, StubDebugAgent
from adapters.maintenance_agent import (
    STUB_MAINTENANCE_PATCH,
    StubMaintenanceAgent,
    StubMaintenanceAgentFailing,
)
from adapters.test_agent import StubTestAgent, StubTestAgentFailing
from aggregation import aggregate
from models import SubAgentInput


_INPUT = SubAgentInput(
    session_id="demo-001",
    repo_path="/fake/demo_target",
    bug_report="average() returns wrong result",
    understanding_summary="buggy_calc/calc.py uses // on line 2",
)

_ALWAYS_OK = lambda _p: True  # noqa: E731


# ---------------------------------------------------------------------------
# Full demo scenario: all three stubs together
# ---------------------------------------------------------------------------

class TestDemoStubsAggregation:
    """
    Runs all three stub agents concurrently and asserts the demo aggregation outcome.

    debug patch (line 2 fix, confidence 0.7) wins despite lower confidence than
    maintenance (0.9) because the test agent's finding on buggy_calc/calc.py:2
    corroborates debug only.
    """

    def _run_all(self):
        async def _gather():
            results = await asyncio.gather(
                StubDebugAgent().run(_INPUT),
                StubTestAgent().run(_INPUT),
                StubMaintenanceAgent().run(_INPUT),
            )
            return list(results)
        return asyncio.run(_gather())

    def test_debug_patch_chosen(self):
        results = self._run_all()
        outcome = aggregate(results, _ALWAYS_OK)
        assert outcome.chosen_patch == STUB_DEBUG_PATCH
        assert outcome.patch_source_agents == ["debug"]

    def test_maintenance_conflict_recorded(self):
        results = self._run_all()
        outcome = aggregate(results, _ALWAYS_OK)
        picked = [
            c for c in outcome.conflicts
            if c.resolution == "picked_debug"
            and "maintenance" in c.agents_involved
        ]
        assert len(picked) == 1

    def test_selection_reason_names_test_agent_with_line(self):
        results = self._run_all()
        outcome = aggregate(results, _ALWAYS_OK)
        assert outcome.selection_reason is not None
        assert "test (finding on buggy_calc/calc.py:2)" in outcome.selection_reason

    def test_no_open_conflicts(self):
        """All agents point at buggy_calc/calc.py — no primary-file disagreement."""
        results = self._run_all()
        outcome = aggregate(results, _ALWAYS_OK)
        open_conflicts = [c for c in outcome.conflicts if c.resolution == "open"]
        assert len(open_conflicts) == 0


# ---------------------------------------------------------------------------
# Failing stub scenarios
# ---------------------------------------------------------------------------

class TestFailingStubs:
    def test_stub_test_agent_failing_raises(self):
        async def _run():
            with pytest.raises(RuntimeError):
                await StubTestAgentFailing().run(_INPUT)
        asyncio.run(_run())

    def test_stub_maintenance_agent_failing_raises(self):
        async def _run():
            with pytest.raises(RuntimeError):
                await StubMaintenanceAgentFailing().run(_INPUT)
        asyncio.run(_run())


# ---------------------------------------------------------------------------
# Template file integrity
# ---------------------------------------------------------------------------

class TestTemplateIntegrity:
    _TEMPLATE_CALC = (
        Path(__file__).parent.parent
        / "demo_repo_template" / "buggy_calc" / "calc.py"
    )

    def test_template_calc_exact_content(self):
        """calc.py must be exactly two lines with 4-space indent and a trailing newline."""
        content = self._TEMPLATE_CALC.read_bytes()
        assert content == b"def average(numbers):\n    return sum(numbers) // len(numbers)\n"

    def test_stub_patches_match_template(self):
        """
        The old-side hunk lines of both stub patches (context and removed lines,
        excluding headers) must match the template file lines in order.
        """
        template_lines = self._TEMPLATE_CALC.read_text(encoding="utf-8").splitlines()

        for patch in (STUB_DEBUG_PATCH, STUB_MAINTENANCE_PATCH):
            hunk_old_lines = [
                line[1:]  # strip leading ' ' or '-'
                for line in patch.splitlines()
                if (line.startswith(" ") or line.startswith("-"))
                and not line.startswith("---")
            ]
            assert hunk_old_lines == template_lines, (
                f"Patch old-side lines do not match template for patch:\n{patch}"
            )
