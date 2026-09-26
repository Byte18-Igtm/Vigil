from __future__ import annotations

# STUB: Debug sub-agent adapter
# Owner: debug-agent team (see STUBS.md)
# Contract: receives SubAgentInput, returns SubAgentResult.
# Replace StubDebugAgent.run() with a real async call when the agent is ready.
#
# NOTE: diff paths use the repo-relative path buggy_calc/calc.py
# (a/buggy_calc/calc.py in diff headers, file="buggy_calc/calc.py" in findings)
# so that corroboration line-matching works correctly against the demo repo.

import asyncio
from datetime import datetime, timezone
from typing import Protocol

from models import EvidenceItem, Finding, SubAgentInput, SubAgentResult


class DebugAgentAdapter(Protocol):  # STUB
    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        ...


# The fix diff: changes // to / on line 2 of buggy_calc/calc.py
STUB_DEBUG_PATCH = (
    "--- a/buggy_calc/calc.py\n"
    "+++ b/buggy_calc/calc.py\n"
    "@@ -1,2 +1,2 @@\n"
    " def average(numbers):\n"
    "-    return sum(numbers) // len(numbers)\n"
    "+    return sum(numbers) / len(numbers)\n"
)

STUB_DEBUG_CONFIDENCE = 0.7


class StubDebugAgent:  # STUB
    """
    Returns a realistic SubAgentResult for the demo bug.
    Confidence is deliberately set lower than the maintenance stub (0.7 vs 0.9)
    so that corroboration by the test agent is what causes debug to win.
    """

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        started = datetime.now(timezone.utc)
        await asyncio.sleep(0)  # yield to event loop
        return SubAgentResult(
            agent="debug",
            status="ok",
            summary=(
                "Found floor division operator (//) in average() at "
                "buggy_calc/calc.py:2. This truncates non-integer results."
            ),
            findings=[
                Finding(
                    file="buggy_calc/calc.py",
                    claim="Floor division (//) truncates fractional averages",
                    confidence=STUB_DEBUG_CONFIDENCE,
                    evidence_ids=["debug-ev-1"],
                    line=2,
                )
            ],
            proposed_patch=STUB_DEBUG_PATCH,
            evidence=[
                EvidenceItem(
                    id="debug-ev-1",
                    type="code_ref",
                    source="debug",
                    content=(
                        "buggy_calc/calc.py line 2: "
                        "return sum(numbers) // len(numbers)"
                    ),
                )
            ],
            error=None,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )
