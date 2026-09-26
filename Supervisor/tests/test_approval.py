from __future__ import annotations

import asyncio
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

import supervisor as sv
from adapters.debug_agent import STUB_DEBUG_PATCH, StubDebugAgent
from adapters.test_agent import StubTestAgent
from aggregation import patch_hash
from models import ApprovalDecision
from state import (
    ApprovalStateError,
    IllegalTransitionError,
    PatchHashMismatchError,
)

TEMPLATE_DIR = Path(__file__).parent.parent / "demo_repo_template"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

def _git(args, cwd, **kwargs):
    return subprocess.run(
        args, cwd=str(cwd), capture_output=True, text=True, shell=False, **kwargs
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


def _decision(session_id, patch_h, decision="approve"):
    return ApprovalDecision(
        session_id=session_id,
        patch_hash=patch_h,
        decision=decision,
        approver="tester",
        timestamp=datetime.now(timezone.utc),
    )


async def _setup_awaiting(repo_path: str):
    """Create session and run investigation; returns (session_id, report)."""
    sid = await sv.create_session(repo_path, "bug", consent_confirmed=True)
    report = await sv.run_investigation(sid)
    assert report.state == "AWAITING_APPROVAL"
    return sid, report


# ---------------------------------------------------------------------------
# _apply_patch before approval raises; repo unchanged and clean
# ---------------------------------------------------------------------------

class TestApplyBeforeApproval:
    def test_apply_patch_before_approval_raises(self, demo_repo):
        async def _run():
            sid = await sv.create_session(str(demo_repo), "bug", consent_confirmed=True)
            await sv.run_investigation(sid)
            # Directly call _apply_patch — session is AWAITING_APPROVAL, not APPROVED
            from state import SessionState
            session = sv._store.get(sid)
            # State is AWAITING_APPROVAL, so _apply_patch must raise
            with pytest.raises((IllegalTransitionError, AssertionError)):
                await sv._apply_patch(session)
            # Repo still clean
            from patching import check_repo
            check_repo(str(demo_repo))  # raises if dirty

        asyncio.run(_run())


# ---------------------------------------------------------------------------
# Hash mismatch raises PatchHashMismatchError
# ---------------------------------------------------------------------------

class TestHashMismatch:
    def test_wrong_hash_raises(self, demo_repo):
        async def _run():
            sid, report = await _setup_awaiting(str(demo_repo))
            bad_decision = _decision(sid, "0" * 64)
            with pytest.raises(PatchHashMismatchError):
                await sv.submit_approval(bad_decision)

        asyncio.run(_run())


# ---------------------------------------------------------------------------
# Approval in wrong state raises ApprovalStateError
# ---------------------------------------------------------------------------

class TestApprovalWrongState:
    def test_approve_before_investigation_raises(self, demo_repo):
        async def _run():
            sid = await sv.create_session(str(demo_repo), "bug", consent_confirmed=True)
            fake_hash = patch_hash(STUB_DEBUG_PATCH)
            with pytest.raises(ApprovalStateError):
                await sv.submit_approval(_decision(sid, fake_hash))

        asyncio.run(_run())


# ---------------------------------------------------------------------------
# Reject → REJECTED; then approve → ApprovalStateError
# ---------------------------------------------------------------------------

class TestRejectThenApprove:
    def test_reject_then_approve_raises(self, demo_repo):
        async def _run():
            sid, report = await _setup_awaiting(str(demo_repo))
            await sv.submit_approval(_decision(sid, report.patch_hash, "reject"))
            # Approve after reject
            with pytest.raises(ApprovalStateError):
                await sv.submit_approval(_decision(sid, report.patch_hash, "approve"))

        asyncio.run(_run())

    def test_reject_no_patch_branch(self, demo_repo):
        async def _run():
            sid, report = await _setup_awaiting(str(demo_repo))
            final = await sv.submit_approval(_decision(sid, report.patch_hash, "reject"))
            assert final.state == "REJECTED"

        asyncio.run(_run())
        # No patchpermit branch created
        r = _git(["git", "branch", "--list", "vigil/*"], cwd=demo_repo)
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Double approve via asyncio.gather → exactly one commit
# ---------------------------------------------------------------------------

class TestDoubleApprove:
    def test_double_approve_exactly_one_commit(self, demo_repo):
        async def _run():
            sid, report = await _setup_awaiting(str(demo_repo))
            d = _decision(sid, report.patch_hash)
            # Submit two approvals concurrently
            r1, r2 = await asyncio.gather(
                sv.submit_approval(d),
                sv.submit_approval(d),
            )
            return r1, r2

        r1, r2 = asyncio.run(_run())
        assert r1.state in ("COMPLETED", "TESTS_FAILED", "APPLYING", "TESTING", "APPROVED")
        assert r2.state in ("COMPLETED", "TESTS_FAILED", "APPLYING", "TESTING", "APPROVED")

        # Exactly one commit beyond the initial commit on the patch branch
        # git rev-list --count HEAD should be 2 (initial + patch commit)
        r = _git(["git", "rev-list", "--count", "HEAD"], cwd=demo_repo)
        assert r.stdout.strip() == "2"
