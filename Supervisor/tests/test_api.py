from __future__ import annotations

"""FastAPI TestClient tests for api.py."""

import asyncio
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import supervisor as sv

TEMPLATE_DIR = Path(__file__).parent.parent / "demo_repo_template"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _git(args, cwd):
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, shell=False)


@pytest.fixture()
def demo_repo(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(
        TEMPLATE_DIR, repo,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )
    _git(["git", "init"], cwd=repo)
    _git(["git", "add", "."], cwd=repo)
    _git(["git", "-c", "user.name=Test", "-c", "user.email=t@t.com",
          "commit", "-m", "initial"], cwd=repo)
    return repo


@pytest.fixture()
def client(demo_repo, monkeypatch):
    """TestClient with ALLOWED_REPO_ROOT set to demo_repo's parent."""
    monkeypatch.setenv("PATCHPERMIT_ALLOWED_REPO_ROOT", str(demo_repo.parent))
    sv.reset_for_tests()
    # Re-import api AFTER env var is set so _allowed_repo_root() is fresh
    import importlib, api as api_mod
    importlib.reload(api_mod)
    with TestClient(api_mod.app, raise_server_exceptions=False) as c:
        yield c
    sv.reset_for_tests()


def _create_and_investigate(client, repo_path):
    r = client.post("/sessions", json={
        "repo_path": str(repo_path),
        "bug_report": "average() returns wrong result",
        "consent_confirmed": True,
    })
    assert r.status_code == 201, r.text
    sid = r.json()["session_id"]
    r2 = client.post(f"/sessions/{sid}/investigate")
    assert r2.status_code == 200, r2.text
    return sid, r2.json()


# ---------------------------------------------------------------------------
# Happy path: create → investigate → AWAITING_APPROVAL
# ---------------------------------------------------------------------------

class TestInvestigate:
    def test_awaiting_approval_with_location_and_patch_hash(self, client, demo_repo):
        sid, report = _create_and_investigate(client, demo_repo)
        assert report["state"] == "AWAITING_APPROVAL"
        assert report["patch_hash"] is not None
        loc = report.get("location")
        assert loc is not None
        assert loc["file"] == "buggy_calc/calc.py"
        assert loc["line"] == 2

    def test_location_context_has_target_line_with_comment(self, client, demo_repo):
        sid, report = _create_and_investigate(client, demo_repo)
        loc = report.get("location")
        assert loc is not None
        ctx = loc.get("context")
        assert ctx is not None and len(ctx) > 0
        target_entries = [e for e in ctx if e.get("target") is True]
        assert len(target_entries) == 1, "exactly one context entry should have target=True"
        assert "//" in target_entries[0]["code"], "target line should contain '//' (integer division)"


# ---------------------------------------------------------------------------
# Approve → COMPLETED
# ---------------------------------------------------------------------------

class TestApprove:
    def test_approve_correct_hash_completed(self, client, demo_repo):
        sid, report = _create_and_investigate(client, demo_repo)
        r = client.post(f"/sessions/{sid}/decision", json={
            "decision": "approve",
            "patch_hash": report["patch_hash"],
            "approver": "tester",
        })
        assert r.status_code == 200, r.text
        final = r.json()
        assert final["state"] == "COMPLETED"
        assert final["test_result"]["ran"] is True
        assert final["test_result"]["passed"] is True
        assert final["branch"] is not None


# ---------------------------------------------------------------------------
# Reject → REJECTED, no patch branch
# ---------------------------------------------------------------------------

class TestReject:
    def test_reject_rejected_no_branch(self, client, demo_repo):
        sid, report = _create_and_investigate(client, demo_repo)
        r = client.post(f"/sessions/{sid}/decision", json={
            "decision": "reject",
            "patch_hash": report["patch_hash"],
            "approver": "tester",
        })
        assert r.status_code == 200, r.text
        final = r.json()
        assert final["state"] == "REJECTED"
        # No patchpermit branch
        branches = _git(["git", "branch", "--list", "vigil/*"], cwd=demo_repo)
        assert branches.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestErrors:
    def test_wrong_hash_409(self, client, demo_repo):
        sid, _ = _create_and_investigate(client, demo_repo)
        r = client.post(f"/sessions/{sid}/decision", json={
            "decision": "approve",
            "patch_hash": "0" * 64,
            "approver": "tester",
        })
        assert r.status_code == 409

    def test_approve_before_investigate_409(self, client, demo_repo):
        r = client.post("/sessions", json={
            "repo_path": str(demo_repo),
            "bug_report": "average() returns wrong result",
            "consent_confirmed": True,
        })
        sid = r.json()["session_id"]
        r2 = client.post(f"/sessions/{sid}/decision", json={
            "decision": "approve",
            "patch_hash": "a" * 64,
            "approver": "tester",
        })
        assert r2.status_code == 409

    def test_unknown_session_404(self, client):
        r = client.get("/sessions/nosuchid")
        assert r.status_code == 404

    def test_consent_false_400(self, client, demo_repo):
        r = client.post("/sessions", json={
            "repo_path": str(demo_repo),
            "bug_report": "bug",
            "consent_confirmed": False,
        })
        assert r.status_code == 400

    def test_repo_outside_root_403(self, client, tmp_path_factory):
        outside = tmp_path_factory.mktemp("outside")
        r = client.post("/sessions", json={
            "repo_path": str(outside),
            "bug_report": "bug",
            "consent_confirmed": True,
        })
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# CORS: disallowed origin gets no allow header
# ---------------------------------------------------------------------------

class TestCORS:
    def test_disallowed_origin_no_allow_header(self, client):
        r = client.get("/health", headers={"Origin": "http://evil.example.com"})
        assert "access-control-allow-origin" not in r.headers

# ---------------------------------------------------------------------------
# Scan endpoint
# ---------------------------------------------------------------------------

class TestScan:
    def test_scan_finds_average_failure(self, client, demo_repo):
        """Scan should detect test_average_float failing and bug_report contains 'average('."""
        r = client.post("/projects/scan", json={"repo_path": str(demo_repo)})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["scan"]["ran"] is True
        assert data["scan"]["passed"] is False
        failures = data["scan"]["failures"]
        assert len(failures) > 0
        names = [f["test"] for f in failures]
        assert any("test_average_float" in n for n in names), f"failures: {names}"
        # bug_report must contain "average("
        assert data["bug_report"] is not None
        assert "average(" in data["bug_report"], f"bug_report: {data['bug_report']}"

    def test_scan_tree_clean_afterwards(self, client, demo_repo):
        """git tree must be clean after a scan (no dirty files)."""
        r = client.post("/projects/scan", json={"repo_path": str(demo_repo)})
        assert r.status_code == 200, r.text
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(demo_repo), capture_output=True, text=True,
        )
        assert status.stdout.strip() == "", f"dirty tree: {status.stdout}"

    def test_scan_outside_root_403(self, client, tmp_path_factory):
        """Scan outside the allowed root must return 403."""
        outside = tmp_path_factory.mktemp("outsiderepo")
        r = client.post("/projects/scan", json={"repo_path": str(outside)})
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Audit endpoint
# ---------------------------------------------------------------------------

class TestAudit:
    def test_audit_entry_on_approve(self, client, demo_repo):
        sid, report = _create_and_investigate(client, demo_repo)
        r = client.post(f"/sessions/{sid}/decision", json={
            "decision": "approve",
            "patch_hash": report["patch_hash"],
            "approver": "alice",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        audit = data.get("audit", [])
        assert len(audit) >= 1
        assert audit[-1]["decision"] == "approve"
        assert audit[-1]["approver"] == "alice"

    def test_audit_entry_on_reject(self, client, demo_repo):
        sid, report = _create_and_investigate(client, demo_repo)
        r = client.post(f"/sessions/{sid}/decision", json={
            "decision": "reject",
            "patch_hash": report["patch_hash"],
            "approver": "bob",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        audit = data.get("audit", [])
        assert len(audit) >= 1
        assert audit[-1]["decision"] == "reject"
        assert audit[-1]["approver"] == "bob"


# ---------------------------------------------------------------------------
# GET /sessions list
# ---------------------------------------------------------------------------

class TestSessionList:
    def test_list_sessions_includes_finished(self, client, demo_repo):
        sid, report = _create_and_investigate(client, demo_repo)
        # Approve to finish it
        client.post(f"/sessions/{sid}/decision", json={
            "decision": "approve",
            "patch_hash": report["patch_hash"],
            "approver": "tester",
        })
        r = client.get("/sessions")
        assert r.status_code == 200, r.text
        sessions = r.json()
        sids = [s["session_id"] for s in sessions]
        assert sid in sids


# ---------------------------------------------------------------------------
# GET /projects
# ---------------------------------------------------------------------------

class TestProjects:
    def test_projects_includes_demo_repo(self, client, demo_repo):
        r = client.get("/projects")
        assert r.status_code == 200, r.text
        projects = r.json()
        names = [p["name"] for p in projects]
        assert "repo" in names, f"projects: {names}"


# ---------------------------------------------------------------------------
# GET /security
# ---------------------------------------------------------------------------

class TestSecurity:
    def test_security_returns_entries(self, client):
        r = client.get("/security")
        assert r.status_code == 200, r.text
        entries = r.json()
        assert isinstance(entries, list)
        assert len(entries) >= 1
        for entry in entries:
            assert "guarantee" in entry
            assert "file" in entry


