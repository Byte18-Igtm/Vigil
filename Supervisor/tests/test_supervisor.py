from __future__ import annotations

import asyncio
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

import supervisor as sv
from adapters.debug_agent import STUB_DEBUG_PATCH, StubDebugAgent
from adapters.fakes import StubSlowAgent
from adapters.test_agent import StubTestAgent
from aggregation import patch_hash
from models import ApprovalDecision
from state import ConsentRequiredError

TEMPLATE_DIR = Path(__file__).parent.parent / "demo_repo_template"


# ---------------------------------------------------------------------------
# Fixture: temp git repo + reset supervisor state
# ---------------------------------------------------------------------------

def _git(args, cwd):
    return subprocess.run(
        args, cwd=str(cwd), capture_output=True, text=True, shell=False,
    )


@pytest.fixture()
def demo_repo(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(
        TEMPLATE_DIR, repo,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )
    _git(["git", "init"], cwd=repo)
    _git(["git", "add", "."], cwd=repo)
    _git([
        "git", "-c", "user.name=PatchPermit", "-c", "user.email=patchpermit@localhost",
        "commit", "-m", "initial",
    ], cwd=repo)
    return repo


@pytest.fixture(autouse=True)
def _reset():
    sv.reset_for_tests()
    yield
    sv.reset_for_tests()


def _approve(session_id: str, patch_h: str) -> ApprovalDecision:
    return ApprovalDecision(
        session_id=session_id,
        patch_hash=patch_h,
        decision="approve",
        approver="tester",
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Consent check
# ---------------------------------------------------------------------------

class TestConsentRequired:
    def test_create_session_without_consent_raises(self, demo_repo):
        with pytest.raises(ConsentRequiredError):
            asyncio.run(sv.create_session(str(demo_repo), "bug", consent_confirmed=False))

    def test_create_session_with_consent_returns_id(self, demo_repo):
        sid = asyncio.run(sv.create_session(str(demo_repo), "bug", consent_confirmed=True))
        assert isinstance(sid, str) and len(sid) > 0


# ---------------------------------------------------------------------------
# Happy path: investigate → approve → COMPLETED
# ---------------------------------------------------------------------------

class TestHappyPath:
    def test_full_flow_completed(self, demo_repo):
        async def _run():
            sid = await sv.create_session(str(demo_repo), "bug", consent_confirmed=True)
            report = await sv.run_investigation(sid)
            assert report.state == "AWAITING_APPROVAL"
            assert report.patch == STUB_DEBUG_PATCH
            decision = _approve(sid, report.patch_hash)
            final = await sv.submit_approval(decision)
            return final

        final = asyncio.run(_run())
        assert final.state == "COMPLETED"
        assert final.test_result is not None
        assert final.test_result.ran is True
        assert final.test_result.passed is True
        assert final.branch is not None
        assert final.branch.startswith("vigil/")


# ---------------------------------------------------------------------------
# Slow agent → timeout → still reaches AWAITING_APPROVAL
# ---------------------------------------------------------------------------

class TestAgentTimeout:
    def test_slow_agent_gets_timeout_status(self, demo_repo):
        async def _run():
            sv.configure(
                agents={
                    "debug": StubDebugAgent(),
                    "test": StubSlowAgent("test", delay_seconds=5.0),
                },
                agent_timeout=0.1,
            )
            sid = await sv.create_session(str(demo_repo), "bug", consent_confirmed=True)
            report = await sv.run_investigation(sid)
            return report

        report = asyncio.run(_run())
        statuses = {e.agent: e.status for e in report.agent_statuses}
        assert statuses["test"] == "timeout"
        # Flow still completes — debug patch survives
        assert report.state == "AWAITING_APPROVAL"


# ---------------------------------------------------------------------------
# Failing test stub → status "failed"
# ---------------------------------------------------------------------------

class TestFailingAgent:
    def test_failing_agent_recorded(self, demo_repo):
        from adapters.test_agent import StubTestAgentFailing
        async def _run():
            sv.configure(agents={
                "debug": StubDebugAgent(),
                "test": StubTestAgentFailing(),
            })
            sid = await sv.create_session(str(demo_repo), "bug", consent_confirmed=True)
            return await sv.run_investigation(sid)

        report = asyncio.run(_run())
        statuses = {e.agent: e.status for e in report.agent_statuses}
        assert statuses["test"] == "failed"
        assert report.state in ("AWAITING_APPROVAL", "NO_PATCH", "FAILED")


# ---------------------------------------------------------------------------
# Dirty repo → FAILED
# ---------------------------------------------------------------------------

class TestDirtyRepo:
    def test_dirty_repo_gives_failed_report(self, demo_repo):
        # Make the tree dirty
        (demo_repo / "buggy_calc" / "calc.py").write_text("dirty\n")

        async def _run():
            sid = await sv.create_session(str(demo_repo), "bug", consent_confirmed=True)
            return await sv.run_investigation(sid)

        report = asyncio.run(_run())
        assert report.state == "FAILED"
        assert report.failure_reason is not None


# ---------------------------------------------------------------------------
# PATCHPERMIT_AGENT_MODE=real → NancyDebugAdapter / NancyTestAdapter used
# ---------------------------------------------------------------------------

class _FakeNancyDebug:
    """Minimal stand-in for NancyDebugAdapter that returns recognisable evidence."""
    async def run(self, inp):
        from datetime import datetime, timezone
        from models import EvidenceItem, Finding, SubAgentResult
        now = datetime.now(timezone.utc)
        return SubAgentResult(
            agent="debug",
            status="ok",
            summary="fake nancy debug",
            findings=[Finding(
                file="buggy_calc/calc.py",
                claim="integer division",
                confidence=0.9,
                evidence_ids=["nancy-debug-ev-1"],
                line=2,
            )],
            proposed_patch=(
                "diff --git a/buggy_calc/calc.py b/buggy_calc/calc.py\n"
                "--- a/buggy_calc/calc.py\n"
                "+++ b/buggy_calc/calc.py\n"
                "@@ -1,2 +1,2 @@\n"
                " def average(numbers):\n"
                "-    return sum(numbers) // len(numbers)\n"
                "+    return sum(numbers) / len(numbers)\n"
            ),
            evidence=[EvidenceItem(
                id="nancy-debug-ev-1",
                type="reasoning",
                source="debug",
                content="nancy-debug: integer division is the bug",
            )],
            error=None,
            started_at=now,
            finished_at=now,
        )


class _FakeNancyTest:
    """Minimal stand-in for NancyTestAdapter that returns recognisable evidence."""
    async def run(self, inp):
        from datetime import datetime, timezone
        from models import EvidenceItem, Finding, SubAgentResult
        now = datetime.now(timezone.utc)
        return SubAgentResult(
            agent="test",
            status="ok",
            summary="fake nancy test",
            findings=[Finding(
                file="buggy_calc/calc.py",
                claim="average should return float",
                confidence=0.8,
                evidence_ids=["nancy-test-ev-1"],
                line=2,
            )],
            proposed_patch=None,
            evidence=[EvidenceItem(
                id="nancy-test-ev-1",
                type="reasoning",
                source="test",
                content="nancy-test: assert average([1,2,3,4]) == 2.5",
            )],
            error=None,
            started_at=now,
            finished_at=now,
        )


class TestRealAgentMode:
    def test_real_mode_uses_nancy_adapters_and_labels_them(self, demo_repo, monkeypatch):
        """
        With PATCHPERMIT_AGENT_MODE=real and fake Nancy adapters injected,
        the report's evidence comes from those adapters and the limitations
        string names the adapter classes (not the stub names).
        """
        monkeypatch.setenv("PATCHPERMIT_AGENT_MODE", "real")
        sv.reset_for_tests()  # picks up new env var → _build_agents() called

        # Replace the Nancy adapters with lightweight fakes (no network/LLM)
        sv.configure(agents={"debug": _FakeNancyDebug(), "test": _FakeNancyTest()})

        async def _run():
            sid = await sv.create_session(str(demo_repo), "average() bug", consent_confirmed=True)
            return await sv.run_investigation(sid)

        report = asyncio.run(_run())

        # Evidence must come from the fake Nancy adapters.
        # The aggregation layer prefixes ids as "debug:<id>" / "test:<id>".
        ev_ids = {e.id for e in report.evidence}
        assert any("nancy-debug-ev-1" in eid or "nancy-test-ev-1" in eid for eid in ev_ids), (
            f"Expected nancy evidence ids, got: {ev_ids}"
        )

        # The limitations label must reflect the actual classes, not the env var text
        mode_lines = [l for l in report.limitations if l.startswith("Agent mode:")]
        assert len(mode_lines) == 1, f"limitations: {report.limitations}"
        label = mode_lines[0]
        assert "_FakeNancyDebug" in label, f"label: {label}"
        assert "_FakeNancyTest" in label, f"label: {label}"
        # Must NOT contain the old hard-coded strings
        assert "real agents" not in label, f"label still uses hard-coded text: {label}"
        assert "demo mode" not in label, f"label still uses hard-coded text: {label}"
