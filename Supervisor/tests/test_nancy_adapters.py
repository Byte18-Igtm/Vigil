from __future__ import annotations

"""
Tests for locator.py and nancy_agents.py.

Skipped entirely if PATCHPERMIT_SUBAGENTS_PATH is unset, since the real
agents require the teammate's LLM engine and API keys.
"""

import asyncio
import os
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# Skip guard
# ---------------------------------------------------------------------------

SUBAGENTS_PATH = os.environ.get("PATCHPERMIT_SUBAGENTS_PATH", "")
pytestmark = pytest.mark.skipif(
    not SUBAGENTS_PATH,
    reason="PATCHPERMIT_SUBAGENTS_PATH is not set — nancy adapter tests skipped",
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TEMPLATE_DIR = Path(__file__).parent.parent / "demo_repo_template"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def demo_repo(tmp_path):
    """Copy demo_repo_template into a fresh temp directory (no git)."""
    repo = tmp_path / "repo"
    shutil.copytree(
        TEMPLATE_DIR, repo,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )
    return repo


@pytest.fixture()
def demo_git_repo(tmp_path):
    """Copy demo_repo_template into a temp git repo with an initial commit."""
    repo = tmp_path / "repo"
    shutil.copytree(
        TEMPLATE_DIR, repo,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )
    subprocess.run(["git", "init"], cwd=str(repo), capture_output=True)
    subprocess.run(["git", "add", "."], cwd=str(repo), capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=t@t.com",
         "commit", "-m", "initial"],
        cwd=str(repo), capture_output=True,
    )
    return repo


# ---------------------------------------------------------------------------
# Fake agent objects (no LLM, no network)
# ---------------------------------------------------------------------------


class _FakeDebugResult:
    def __init__(self, status="completed", suggested_fix="", detected_issue="floor div",
                 evidence_reasoning="uses //", justification="use /",
                 confidence="high", error=None):
        self.status = status
        self.error = error
        self.summary = f"Debug analysis: {detected_issue}"
        self.debugData = _FakeDebugPayload(
            suggestedFix=suggested_fix,
            detectedIssue=detected_issue,
            evidenceReasoning=evidence_reasoning,
            justification=justification,
            confidence=confidence,
        ) if status == "completed" else None


class _FakeDebugPayload:
    def __init__(self, suggestedFix, detectedIssue, evidenceReasoning,
                 justification, confidence):
        self.suggestedFix = suggestedFix
        self.detectedIssue = detectedIssue
        self.evidenceReasoning = evidenceReasoning
        self.justification = justification
        self.confidence = confidence


class _FakeTestResult:
    def __init__(self, status="completed", what="test average", expected="2.5",
                 generated="def test(): pass", error=None):
        self.status = status
        self.error = error
        self.summary = f"Test plan generated: 1 cases formulated"
        self.testData = _FakeTestPayload(
            whatShouldBeTested=what,
            expectedBehavior=expected,
            generatedTestCode=generated,
        ) if status == "completed" else None


class _FakeTestPayload:
    def __init__(self, whatShouldBeTested, expectedBehavior, generatedTestCode):
        self.whatShouldBeTested = whatShouldBeTested
        self.expectedBehavior = expectedBehavior
        self.generatedTestCode = generatedTestCode


def _fake_task():
    """Return a minimal object with .timestamp attribute."""
    import time
    class _T:
        timestamp = time.time()
        id = "fake-task-id"
    return _T()


# ---------------------------------------------------------------------------
# Locator tests
# ---------------------------------------------------------------------------


class TestLocator:
    def test_finds_average_in_demo_repo(self, demo_repo):
        from adapters.locator import locate
        result = locate(str(demo_repo), "average() returns wrong result")
        assert result == ("buggy_calc/calc.py", 2)

    def test_returns_none_when_nothing_matches(self, demo_repo):
        from adapters.locator import locate
        result = locate(str(demo_repo), "this references no_such_function()")
        assert result is None


# ---------------------------------------------------------------------------
# _build_diff tests (tested via nancy_agents internals)
# ---------------------------------------------------------------------------


class TestBuildDiff:
    def _calc_lines(self):
        """Lines of demo_repo_template/buggy_calc/calc.py as list with newlines."""
        return [
            "def average(numbers):\n",
            "    return sum(numbers) // len(numbers)\n",
        ]

    def test_fix_produces_valid_patch(self, demo_git_repo):
        """A real unindented fix is re-indented and passes git apply --check."""
        from adapters.nancy_agents import _build_diff
        file_lines = self._calc_lines()
        diff, err = _build_diff(
            "buggy_calc/calc.py",
            file_lines,
            2,
            "return sum(numbers) / len(numbers)",  # no indent — must be re-indented
        )
        assert err is None
        assert diff is not None
        assert diff.endswith("\n")
        # Apply to git repo
        r = subprocess.run(
            ["git", "apply", "--check", "-"],
            cwd=str(demo_git_repo),
            input=diff,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"git apply --check failed:\n{r.stderr}\n---diff---\n{diff}"

    def test_multiline_fix_reindented(self):
        from adapters.nancy_agents import _build_diff
        file_lines = [
            "def average(numbers):\n",
            "    return sum(numbers) // len(numbers)\n",
        ]
        multi_fix = "total = sum(numbers)\ncount = len(numbers)\nreturn total / count"
        diff, err = _build_diff("buggy_calc/calc.py", file_lines, 2, multi_fix)
        assert err is None
        assert diff is not None
        # All replacement lines should start with 4 spaces (matching original indent)
        added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        for line in added:
            assert line.startswith("    "), f"Line not re-indented: {line!r}"

    def test_empty_fix_returns_error(self):
        from adapters.nancy_agents import _build_diff
        _, err = _build_diff("buggy_calc/calc.py", self._calc_lines(), 2, "")
        assert err is not None
        assert "empty" in err.lower()

    def test_identical_fix_returns_error(self):
        from adapters.nancy_agents import _build_diff
        _, err = _build_diff(
            "buggy_calc/calc.py", self._calc_lines(), 2,
            "return sum(numbers) // len(numbers)"  # same as original after strip
        )
        assert err is not None
        assert "identical" in err.lower()

    def test_comment_only_fix_returns_error(self):
        from adapters.nancy_agents import _build_diff
        _, err = _build_diff("buggy_calc/calc.py", self._calc_lines(), 2, "# just a comment")
        assert err is not None
        assert "comment" in err.lower()

    # ------------------------------------------------------------------
    # New tests for whole-function replacement, syntax check, no-op check
    # ------------------------------------------------------------------

    def test_whole_function_fix_applies_and_has_one_def(self, demo_git_repo):
        """
        A suggestedFix that is the whole function body passes git apply --check,
        the patched file contains exactly one 'def average', and the repo's own
        tests pass after applying it.
        """
        from adapters.nancy_agents import _build_diff
        file_lines = self._calc_lines()
        whole_fn_fix = (
            "def average(numbers):\n"
            "    return sum(numbers) / len(numbers)\n"
        )
        diff, err = _build_diff("buggy_calc/calc.py", file_lines, 2, whole_fn_fix)
        assert err is None, f"unexpected error: {err}"
        assert diff is not None
        assert diff.endswith("\n")

        # Must pass git apply --check
        r = subprocess.run(
            ["git", "apply", "--check", "-"],
            cwd=str(demo_git_repo),
            input=diff,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"git apply --check failed:\n{r.stderr}\ndiff:\n{diff}"

        # Apply the patch and check the patched file
        subprocess.run(
            ["git", "apply", "-"],
            cwd=str(demo_git_repo),
            input=diff,
            capture_output=True,
            text=True,
        )
        patched = (demo_git_repo / "buggy_calc" / "calc.py").read_text()
        def_count = patched.count("def average")
        assert def_count == 1, f"expected 1 'def average', got {def_count}:\n{patched}"

        # The repo's own tests must pass with the patch applied
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=str(demo_git_repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"tests failed after applying patch:\n{result.stdout}{result.stderr}"
        )

    def test_invalid_python_fix_returns_failed(self):
        """A syntactically invalid suggestedFix must return an error."""
        from adapters.nancy_agents import _build_diff
        file_lines = self._calc_lines()
        bad_fix = "def average(numbers:\n    return sum(numbers) / len(numbers)\n"
        diff, err = _build_diff("buggy_calc/calc.py", file_lines, 2, bad_fix)
        assert diff is None
        assert err is not None
        assert "valid python" in err.lower(), f"unexpected error message: {err}"

    def test_comment_only_addition_with_same_code_returns_failed(self):
        """
        A fix that adds a comment line then repeats the original code verbatim
        (no actual code change) must return 'suggested fix makes no code change'.
        """
        from adapters.nancy_agents import _build_diff
        file_lines = self._calc_lines()
        # comment line + the exact same return statement — net code change is zero
        no_op_fix = "# Ensure explicit return typing:\nreturn sum(numbers) // len(numbers)"
        diff, err = _build_diff("buggy_calc/calc.py", file_lines, 2, no_op_fix)
        assert diff is None
        assert err is not None
        assert "no code change" in err.lower(), f"unexpected error message: {err}"


# ---------------------------------------------------------------------------
# NancyDebugAdapter tests (fake execute)
# ---------------------------------------------------------------------------


class TestNancyDebugAdapter:
    def _make_adapter_with_fake(self, fake_result):
        """Return a NancyDebugAdapter whose execute() returns fake_result."""
        from adapters.nancy_agents import NancyDebugAdapter

        class _FakeDebugAgent:
            def execute(self, task):
                fake_result._task = task
                return fake_result

        adapter = NancyDebugAdapter.__new__(NancyDebugAdapter)

        original_run = NancyDebugAdapter.run

        async def patched_run(self, inp):
            # Monkey-patch the import functions
            import adapters.nancy_agents as na
            _orig_import = na._import_debug_agent

            def _fake_import():
                class _FakeAgentTask:
                    def __init__(self, **kwargs):
                        import time
                        for k, v in kwargs.items():
                            setattr(self, k, v)
                        self.timestamp = time.time()
                return _FakeDebugAgent, _FakeAgentTask

            na._import_debug_agent = _fake_import
            try:
                return await original_run(self, inp)
            finally:
                na._import_debug_agent = _orig_import

        adapter.run = lambda inp: patched_run(adapter, inp)
        return adapter

    def _inp(self, repo_path):
        from models import SubAgentInput
        return SubAgentInput(
            session_id="t1",
            repo_path=str(repo_path),
            bug_report="average() returns wrong result",
            understanding_summary="",
        )

    def test_failed_agent_status_propagates(self, demo_repo):
        fake = _FakeDebugResult(status="failed", error="LLM error")
        adapter = self._make_adapter_with_fake(fake)
        result = asyncio.run(adapter.run(self._inp(demo_repo)))
        assert result.status == "failed"
        assert result.proposed_patch is None

    def test_execute_raising_propagates(self, demo_repo):
        """When execute() raises, the supervisor records 'failed' and continues."""
        from models import SubAgentInput
        import adapters.nancy_agents as na

        class _RaisingAgent:
            def execute(self, task):
                raise RuntimeError("LLM unavailable")

        class _FakeAgentTask:
            def __init__(self, **kwargs):
                import time
                for k, v in kwargs.items():
                    setattr(self, k, v)
                self.timestamp = time.time()

        _orig = na._import_debug_agent
        na._import_debug_agent = lambda: (_RaisingAgent, _FakeAgentTask)
        try:
            adapter = na.NancyDebugAdapter()
            with pytest.raises(Exception):
                asyncio.run(adapter.run(self._inp(demo_repo)))
        finally:
            na._import_debug_agent = _orig


# ---------------------------------------------------------------------------
# NancyTestAdapter: finding on same line, no patch
# ---------------------------------------------------------------------------


class TestNancyTestAdapter:
    def _inp(self, repo_path):
        from models import SubAgentInput
        return SubAgentInput(
            session_id="t2",
            repo_path=str(repo_path),
            bug_report="average() returns wrong result",
            understanding_summary="",
        )

    def test_test_adapter_no_patch_finding_on_target_line(self, demo_repo):
        import adapters.nancy_agents as na

        class _FakeTestAgent:
            def execute(self, task):
                return _FakeTestResult(
                    status="completed",
                    what="average should return float",
                    expected="2.5 for [1,2,3,4]",
                    generated="def test_avg(): assert average([1,2,3,4]) == 2.5",
                )

        class _FakeAgentTask:
            def __init__(self, **kwargs):
                import time
                for k, v in kwargs.items():
                    setattr(self, k, v)
                self.timestamp = time.time()

        _orig = na._import_test_agent
        na._import_test_agent = lambda: (_FakeTestAgent, _FakeAgentTask)
        try:
            adapter = na.NancyTestAdapter()
            result = asyncio.run(adapter.run(self._inp(demo_repo)))
        finally:
            na._import_test_agent = _orig

        assert result.status == "ok"
        assert result.proposed_patch is None
        assert len(result.findings) == 1
        assert result.findings[0].file == "buggy_calc/calc.py"
        assert result.findings[0].line == 2
        assert result.findings[0].confidence == 0.8


# ---------------------------------------------------------------------------
# Integration: debug + test adapters → aggregation selects debug patch
# ---------------------------------------------------------------------------


class TestNancyAggregationIntegration:
    def test_debug_patch_corroborated_by_test(self, demo_repo):
        """
        Fake debug and test adapters together: aggregate() must select the debug
        patch as corroborated by the test agent's finding on the same line.
        """
        import adapters.nancy_agents as na
        from aggregation import aggregate
        from models import SubAgentInput

        inp = SubAgentInput(
            session_id="t3",
            repo_path=str(demo_repo),
            bug_report="average() returns wrong result",
            understanding_summary="",
        )

        class _FakeDebugAgent:
            def execute(self, task):
                return _FakeDebugResult(
                    status="completed",
                    suggested_fix="return sum(numbers) / len(numbers)",
                    detected_issue="floor division bug",
                    confidence="high",
                )

        class _FakeTestAgent2:
            def execute(self, task):
                return _FakeTestResult(
                    status="completed",
                    what="average should return float",
                )

        class _FakeAgentTask:
            def __init__(self, **kwargs):
                import time
                for k, v in kwargs.items():
                    setattr(self, k, v)
                self.timestamp = time.time()

        _orig_d = na._import_debug_agent
        _orig_t = na._import_test_agent
        na._import_debug_agent = lambda: (_FakeDebugAgent, _FakeAgentTask)
        na._import_test_agent = lambda: (_FakeTestAgent2, _FakeAgentTask)
        try:
            async def _run():
                d = await na.NancyDebugAdapter().run(inp)
                t = await na.NancyTestAdapter().run(inp)
                return [d, t]
            results = asyncio.run(_run())
        finally:
            na._import_debug_agent = _orig_d
            na._import_test_agent = _orig_t

        outcome = aggregate(results, lambda _: True)
        assert outcome.chosen_patch is not None
        assert outcome.patch_source_agents == ["debug"]
        # Test agent corroborates (same file, same line)
        assert outcome.selection_reason is not None
        assert "test" in outcome.selection_reason
