from __future__ import annotations

# STUB: Maintenance sub-agent adapter
# Owner: maintenance-agent team (see STUBS.md)
# Contract: receives SubAgentInput, returns SubAgentResult.
# Replace StubMaintenanceAgent.run() with a real async call when ready.
#
# This stub returns a CONFLICTING patch (renames the function on line 1)
# with HIGHER confidence (0.9) than the debug stub (0.7). The test agent's
# finding on line 2 corroborates the debug patch but NOT this one, so the
# debug patch should win despite lower confidence.
#
# StubMaintenanceAgentFailing raises for the "agent raises" test scenario.

import asyncio
from datetime import datetime, timezone
from typing import Protocol

from models import EvidenceItem, Finding, SubAgentInput, SubAgentResult


class MaintenanceAgentAdapter(Protocol):  # STUB
    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        ...


# Conflicting patch: renames function on line 1, does NOT fix the // bug
STUB_MAINTENANCE_PATCH = (
    "--- a/buggy_calc/calc.py\n"
    "+++ b/buggy_calc/calc.py\n"
    "@@ -1,2 +1,2 @@\n"
    "-def average(numbers):\n"
    "+def mean(numbers):\n"
    "     return sum(numbers) // len(numbers)\n"
)

STUB_MAINTENANCE_CONFIDENCE = 0.9  # higher than debug — corroboration must decide


class StubMaintenanceAgent:  # STUB
    """
    Returns a conflicting patch (rename on line 1) with higher confidence
    than the debug stub. The demo scenario asserts the debug patch wins anyway
    because the test agent corroborates it.
    """

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        started = datetime.now(timezone.utc)
        await asyncio.sleep(0)
        return SubAgentResult(
            agent="maintenance",
            status="ok",
            summary=(
                "average() is ambiguously named; recommend renaming to mean(). "
                "Also detected floor division on line 2."
            ),
            findings=[
                Finding(
                    file="buggy_calc/calc.py",
                    claim="Function name 'average' is ambiguous; should be 'mean'",
                    confidence=STUB_MAINTENANCE_CONFIDENCE,
                    evidence_ids=["maint-ev-1"],
                    line=1,
                )
            ],
            proposed_patch=STUB_MAINTENANCE_PATCH,
            evidence=[
                EvidenceItem(
                    id="maint-ev-1",
                    type="reasoning",
                    source="maintenance",
                    content=(
                        "buggy_calc/calc.py line 1: def average(numbers) — "
                        "naming convention suggests 'mean' for arithmetic mean."
                    ),
                )
            ],
            error=None,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )


class StubMaintenanceAgentFailing:  # STUB — alternate scenario for tests
    """Simulates a maintenance agent that raises an exception."""

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        raise RuntimeError("Maintenance agent unavailable")
