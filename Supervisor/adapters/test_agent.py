from __future__ import annotations

# STUB: Test sub-agent adapter
# Owner: test-agent team (see STUBS.md)
# Contract: receives SubAgentInput, returns SubAgentResult.
# Replace StubTestAgent.run() with a real async call when the agent is ready.
#
# This stub returns NO proposed_patch and a finding on buggy_calc/calc.py line 2,
# which corroborates the debug agent's patch (same file, same line).
# StubTestAgentFailing simulates agent failure for tests.

import asyncio
from datetime import datetime, timezone
from typing import Protocol

from models import EvidenceItem, Finding, SubAgentInput, SubAgentResult


class TestAgentAdapter(Protocol):  # STUB
    __test__ = False  # prevent pytest from collecting this Protocol class

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        ...


class StubTestAgent:  # STUB
    """
    Returns a corroborating finding on buggy_calc/calc.py line 2 with no patch.
    Confidence 0.8 — higher than debug's 0.7, so corroboration (not confidence)
    must be what wins the demo scenario.
    """

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        started = datetime.now(timezone.utc)
        await asyncio.sleep(0)
        return SubAgentResult(
            agent="test",
            status="ok",
            summary=(
                "test_average_float fails: expected 2.5, got 2. "
                "The failure originates in buggy_calc/calc.py line 2."
            ),
            findings=[
                Finding(
                    file="buggy_calc/calc.py",
                    claim="average() returns integer instead of float",
                    confidence=0.8,
                    evidence_ids=["test-ev-1"],
                    line=2,
                )
            ],
            proposed_patch=None,
            evidence=[
                EvidenceItem(
                    id="test-ev-1",
                    type="test_output",
                    source="test",
                    content=(
                        "FAILED tests/test_calc.py::test_average_float — "
                        "AssertionError: assert 2 == 2.5"
                    ),
                )
            ],
            error=None,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )


class StubTestAgentFailing:  # STUB — alternate scenario for tests
    """Simulates a test agent that raises an exception."""

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        raise RuntimeError("Test agent unavailable")
