from __future__ import annotations

import os
import shlex
import subprocess
import sys
import time
from typing import Optional, Tuple

from aggregation import patch_hash
from models import TestRunResult
from redaction import redact
from state import PatchPermitError


class PatchingError(PatchPermitError):
    pass


# ---------------------------------------------------------------------------
# Internal subprocess helper
# ---------------------------------------------------------------------------

def _run(
    args,
    cwd: str,
    input: Optional[str] = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=cwd,
        input=input,
        capture_output=True,
        text=True,
        shell=False,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Public sync functions (called via asyncio.to_thread in supervisor.py)
# ---------------------------------------------------------------------------

def check_repo(repo_path: str) -> None:
    """
    Raise PatchingError if repo_path is not a git work tree or has uncommitted changes.
    Never touches uncommitted work.
    """
    try:
        r = _run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_path,
        )
    except FileNotFoundError:
        raise PatchingError("git is not installed or not on PATH.")
    except subprocess.TimeoutExpired:
        raise PatchingError("git rev-parse timed out.")

    if r.returncode != 0 or r.stdout.strip() != "true":
        raise PatchingError(f"{repo_path!r} is not a git work tree.")

    r2 = _run(["git", "status", "--porcelain"], cwd=repo_path)
    if r2.stdout.strip():
        raise PatchingError(
            "Working tree has uncommitted changes. "
            "Commit or stash them before applying a patch."
        )


def apply_check(repo_path: str, patch: str) -> bool:
    """
    Return True if the patch applies cleanly (git apply --check).
    Returns False on any failure; never raises.
    """
    try:
        r = _run(
            ["git", "apply", "--check", "-"],
            cwd=repo_path,
            input=patch,
        )
        return r.returncode == 0
    except Exception:
        return False


def apply_and_commit(
    repo_path: str,
    patch: str,
    session_id: str,
) -> Tuple[str, str]:
    """
    Apply patch on a new branch and commit.
    Returns (start_branch, new_branch).
    Raises PatchingError on any failure; rolls back to start_branch and
    deletes the new branch before raising.
    """
    new_branch = f"vigil/{session_id[:8]}"

    # Record starting branch
    r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if r.returncode != 0:
        raise PatchingError(f"Could not determine current branch: {r.stderr.strip()}")
    start_branch = r.stdout.strip()

    def _rollback(created_branch: bool) -> None:
        try:
            _run(["git", "checkout", start_branch], cwd=repo_path)
        except Exception:
            pass
        if created_branch:
            try:
                _run(["git", "branch", "-D", new_branch], cwd=repo_path)
            except Exception:
                pass

    # Create new branch
    r = _run(["git", "checkout", "-b", new_branch], cwd=repo_path)
    if r.returncode != 0:
        raise PatchingError(f"Could not create branch {new_branch!r}: {r.stderr.strip()}")

    # Apply patch
    r = _run(["git", "apply", "-"], cwd=repo_path, input=patch)
    if r.returncode != 0:
        _rollback(created_branch=True)
        raise PatchingError(f"git apply failed: {r.stderr.strip()}")

    # Stage all changes
    r = _run(["git", "add", "-A"], cwd=repo_path)
    if r.returncode != 0:
        _rollback(created_branch=True)
        raise PatchingError(f"git add failed: {r.stderr.strip()}")

    # Commit
    r = _run(
        [
            "git",
            "-c", "user.name=Vigil",
            "-c", "user.email=vigil@localhost",
            "commit", "-m", f"Vigil: apply patch for session {session_id[:8]}",
        ],
        cwd=repo_path,
    )
    if r.returncode != 0:
        _rollback(created_branch=True)
        raise PatchingError(f"git commit failed: {r.stderr.strip()}")

    return start_branch, new_branch


def restore_branch(repo_path: str, start_branch: str) -> None:
    """
    Check out start_branch. Used on TESTS_FAILED; the patch branch is kept for inspection.
    """
    r = _run(["git", "checkout", start_branch], cwd=repo_path)
    if r.returncode != 0:
        raise PatchingError(
            f"Could not restore branch {start_branch!r}: {r.stderr.strip()}"
        )


def run_tests(repo_path: str) -> TestRunResult:
    """
    Run the test suite in repo_path.
    Command: PATCHPERMIT_TEST_CMD env var (shlex.split) or [sys.executable, "-m", "pytest", "-q"].
    Timeout: PATCHPERMIT_TEST_TIMEOUT_SEC env var (default 120).
    Returns a TestRunResult; never raises.
    """
    raw_cmd = os.environ.get("PATCHPERMIT_TEST_CMD", "")
    if raw_cmd.strip():
        try:
            cmd = shlex.split(raw_cmd)
        except ValueError:
            return TestRunResult(
                ran=False, passed=False,
                command=raw_cmd, exit_code=None,
                output_tail="Failed to parse PATCHPERMIT_TEST_CMD.",
                duration=None,
            )
    else:
        cmd = [sys.executable, "-m", "pytest", "-q"]

    try:
        timeout_sec = int(os.environ.get("PATCHPERMIT_TEST_TIMEOUT_SEC", "120"))
    except ValueError:
        timeout_sec = 120

    command_str = " ".join(cmd)
    start = time.monotonic()

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout_sec,
        )
        duration = time.monotonic() - start
        raw_output = result.stdout + result.stderr
        tail_lines = raw_output.splitlines()[-100:]
        output_tail = redact("\n".join(tail_lines))
        passed = result.returncode == 0
        return TestRunResult(
            ran=True,
            passed=passed,
            command=command_str,
            exit_code=result.returncode,
            output_tail=output_tail,
            duration=duration,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return TestRunResult(
            ran=True,
            passed=False,
            command=command_str,
            exit_code=None,
            output_tail=f"Test run timed out after {timeout_sec}s.",
            duration=duration,
        )
    except FileNotFoundError:
        return TestRunResult(
            ran=False,
            passed=False,
            command=command_str,
            exit_code=None,
            output_tail=f"Command not found: {cmd[0]!r}",
            duration=None,
        )
    except Exception as exc:
        return TestRunResult(
            ran=False,
            passed=False,
            command=command_str,
            exit_code=None,
            output_tail=f"Unexpected error starting tests: {type(exc).__name__}",
            duration=None,
        )


# ---------------------------------------------------------------------------
# scan_project: run the project's test suite and report failures
# ---------------------------------------------------------------------------

def scan_project(repo_path: str) -> dict:
    """
    Run the project's test suite with -p no:cacheprovider and
    PYTHONDONTWRITEBYTECODE=1. Return a dict:
      {ran, passed, failures:[{test, message, file, line}], output_tail}
    Afterwards asserts the git tree is clean; returns an error entry if not.
    """
    import os as _os
    import re as _re
    import subprocess as _sp
    import time as _time

    env = _os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        timeout_sec = int(_os.environ.get("PATCHPERMIT_TEST_TIMEOUT_SEC", "120"))
    except ValueError:
        timeout_sec = 120

    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
           "--tb=short"]
    start = _time.monotonic()
    try:
        result = _sp.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout_sec,
            env=env,
        )
    except _sp.TimeoutExpired:
        return {
            "ran": True,
            "passed": False,
            "failures": [],
            "output_tail": f"Test run timed out after {timeout_sec}s.",
            "error": "Test run timed out.",
        }
    except Exception as exc:
        return {
            "ran": False,
            "passed": False,
            "failures": [],
            "output_tail": f"Failed to start tests: {type(exc).__name__}",
            "error": f"Failed to start tests: {type(exc).__name__}",
        }

    raw = result.stdout + result.stderr
    tail_lines = raw.splitlines()[-100:]
    output_tail = redact("\n".join(tail_lines))
    passed = result.returncode == 0

    # Parse failures from pytest --tb=short output
    failures = []
    # Pattern: FAILED tests/test_foo.py::test_name - AssertionError: ...
    failed_re = _re.compile(r"^FAILED (.+?)::(.+?)\s+-\s+(.+)$", _re.MULTILINE)
    for m in failed_re.finditer(raw):
        rel_file, test_fn, message = m.group(1), m.group(2), m.group(3)
        # Try to extract file:line from tb lines like "  file.py:42: AssertionError"
        file_line_re = _re.compile(
            _re.escape(rel_file) + r":(\d+): \w+"
        )
        line_match = file_line_re.search(raw)
        line_no = int(line_match.group(1)) if line_match else None
        # Extract the assertion SOURCE line (e.g. "assert average([1,2,3,4]) == 2.5")
        # from the traceback. In pytest --tb=short, source lines appear without
        # the "E " prefix, immediately before the "E  assert ..." evaluated line.
        assert_line = None
        raw_lines = raw.splitlines()
        for idx, rl in enumerate(raw_lines):
            stripped = rl.strip()
            # Look for source lines containing "assert" that are NOT "E " prefixed
            if "assert " in stripped and not stripped.startswith("E ") and not stripped.startswith("E\t"):
                # Make sure we're in a traceback context (previous line references file:line)
                if idx > 0 and _re.search(r"\.py:\d+:", raw_lines[idx - 1]):
                    assert_line = stripped
                    break
        # Fallback: look for "E   assert ..." (evaluated) if no source line found
        if assert_line is None:
            for rl in raw_lines:
                stripped = rl.strip()
                if (stripped.startswith("E ") or stripped.startswith("E\t")) and "assert " in stripped:
                    assert_line = stripped[2:].strip()
                    break

        full_message = message
        if assert_line:
            full_message = assert_line

        failures.append({
            "test": f"{rel_file}::{test_fn}",
            "message": full_message,
            "file": rel_file,
            "line": line_no,
        })

    # Check git tree is clean
    try:
        git_status = _sp.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            shell=False,
            timeout=15,
        )
        if git_status.stdout.strip():
            return {
                "ran": ran if (ran := True) else False,
                "passed": False,
                "failures": failures,
                "output_tail": output_tail,
                "error": "Working tree is dirty after test run. Aborting.",
            }
    except Exception:
        pass  # git not available; skip check

    return {
        "ran": True,
        "passed": passed,
        "failures": failures,
        "output_tail": output_tail,
    }
