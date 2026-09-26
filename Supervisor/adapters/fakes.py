from __future__ import annotations

# STUB — test-only fakes. Not part of the demo path.
# Used by tests/test_approval.py and tests/test_supervisor.py to simulate
# slow agents for the supervisor timeout test (step 6).

import asyncio
from datetime import datetime, timezone

from models import SubAgentInput, SubAgentResult


class StubSlowAgent:  # STUB — test-only
    """
    Sleeps for delay_seconds then returns a minimal ok SubAgentResult.
    Used to test asyncio.wait_for timeout handling in the supervisor.

    agent_name: one of "debug", "test", "maintenance"
    delay_seconds: how long to sleep before returning
    """

    def __init__(self, agent_name: str, delay_seconds: float) -> None:
        self.agent_name = agent_name
        self.delay_seconds = delay_seconds

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        started = datetime.now(timezone.utc)
        await asyncio.sleep(self.delay_seconds)
        return SubAgentResult(
            agent=self.agent_name,
            status="ok",
            summary=f"{self.agent_name} completed after {self.delay_seconds}s",
            findings=[],
            proposed_patch=None,
            evidence=[],
            error=None,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )
