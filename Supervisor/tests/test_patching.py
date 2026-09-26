from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from adapters.debug_agent import STUB_DEBUG_PATCH
from adapters.maintenance_agent import STUB_MAINTENANCE_PATCH
from patching import (
    PatchingError,
    apply_and_commit,
    apply_check,
    check_repo,
    restore_branch,
    run_tests,
)

TEMPLATE_DIR = Path(__file__).parent.parent / "demo_repo_template"


# ---------------------------------------------------------------------------
# Fixture: temp git repo built from the template
# ---------------------------------------------------------------------------

def _git(args, cwd, input=None):
    return subprocess.run(
        args, cwd=str(cwd), input=input,
        capture_output=True, text=True, shell=False,
    )


@pytest.fixture()
def demo_repo(tmp_path):
    """Copy template to tmp_path, git init, initial commit. Returns Path."""
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


# ---------------------------------------------------------------------------
# apply_check tests
# ---------------------------------------------------------------------------

class TestApplyCheck:
    def test_debug_patch_passes(self, demo_repo):
        assert apply_check(str(demo_repo), STUB_DEBUG_PATCH) is True

    def test_maintenance_patch_passes(self, demo_repo):
        assert apply_check(str(demo_repo), STUB_MAINTENANCE_PATCH) is True

    def test_malformed_patch_fails(self, demo_repo):
        assert apply_check(str(demo_repo), "this is not a patch\n") is False


# ---------------------------------------------------------------------------
# check_repo tests
# ---------------------------------------------------------------------------

class TestCheckRepo:
    def test_dirty_tree_raises(self, demo_repo):
        (demo_repo / "buggy_calc" / "calc.py").write_text("dirty\n")
        with pytest.raises(PatchingError, match="uncommitted"):
            check_repo(str(demo_repo))

    def test_non_git_dir_raises(self, tmp_path):
        non_git = tmp_path / "notgit"
        non_git.mkdir()
        with pytest.raises(PatchingError):
            check_repo(str(non_git))


# ---------------------------------------------------------------------------
# apply_and_commit + run_tests: debug patch → tests pass → COMPLETED
# ---------------------------------------------------------------------------

class TestApplyDebugPatch:
    def test_debug_patch_tests_pass(self, demo_repo):
        check_repo(str(demo_repo))
        start_branch, new_branch = apply_and_commit(
            str(demo_repo), STUB_DEBUG_PATCH, "testsess1"
        )
        assert new_branch == "vigil/testsess1"[:len("vigil/") + 8]
        result = run_tests(str(demo_repo))
        assert result.ran is True
        assert result.passed is True
        assert result.exit_code == 0
        # Confirm we are on the patch branch
        r = _git(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=demo_repo)
        assert r.stdout.strip() == new_branch


# ---------------------------------------------------------------------------
# Maintenance patch → tests fail → restore_branch → back on start branch, clean
# ---------------------------------------------------------------------------

class TestApplyMaintenancePatch:
    def test_maintenance_patch_tests_fail_and_restore(self, demo_repo):
        check_repo(str(demo_repo))
        r = _git(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=demo_repo)
        start_branch = r.stdout.strip()

        _start, new_branch = apply_and_commit(
            str(demo_repo), STUB_MAINTENANCE_PATCH, "testsess2"
        )
        result = run_tests(str(demo_repo))
        assert result.ran is True
        assert result.passed is False

        restore_branch(str(demo_repo), start_branch)

        # Back on start branch
        r2 = _git(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=demo_repo)
        assert r2.stdout.strip() == start_branch

        # Working tree is clean
        r3 = _git(["git", "status", "--porcelain"], cwd=demo_repo)
        assert r3.stdout.strip() == ""


# ---------------------------------------------------------------------------
# test_reporting: bad PATCHPERMIT_TEST_CMD → ran=False
# ---------------------------------------------------------------------------

class TestTestCommand:
    def test_nonexistent_command_ran_false(self, demo_repo, monkeypatch):
        monkeypatch.setenv("PATCHPERMIT_TEST_CMD", "nonexistent-command-xyz --flag")
        result = run_tests(str(demo_repo))
        assert result.ran is False
        assert result.passed is False

    def test_apply_check_bad_patch_fails_apply_then_rollback(self, demo_repo):
        """A patch failing git apply --check at apply time → FAILED, repo unchanged."""
        bad_patch = (
            "--- a/buggy_calc/calc.py\n"
            "+++ b/buggy_calc/calc.py\n"
            "@@ -99,2 +99,2 @@\n"
            "-nonexistent line\n"
            "+replacement\n"
        )
        # apply_check returns False
        assert apply_check(str(demo_repo), bad_patch) is False
        # apply_and_commit raises PatchingError
        with pytest.raises(PatchingError):
            apply_and_commit(str(demo_repo), bad_patch, "testsess3")
        # repo is unchanged and clean
        check_repo(str(demo_repo))
