from __future__ import annotations

# Adapters that call the teammate's (Nancy's) real agents.
# Activated when PATCHPERMIT_AGENT_MODE=real.
#
# STUB marker: replace the locate() call with a richer heuristic once the
# teammate's agent API is known to be stable.

import ast
import asyncio
import difflib
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from adapters.locator import locate
from models import EvidenceItem, Finding, SubAgentInput, SubAgentResult


# ---------------------------------------------------------------------------
# Lazy import of teammate code
# ---------------------------------------------------------------------------

def _load_subagents_path() -> str:
    path = os.environ.get("PATCHPERMIT_SUBAGENTS_PATH", "")
    if not path:
        raise ImportError(
            "PATCHPERMIT_SUBAGENTS_PATH is not set. "
            "Set it to the absolute path of the Subagents directory."
        )
    if path not in sys.path:
        sys.path.append(path)
    return path


def _get_engine():
    """Return a GroqEngine if GROQ_API_KEY is set, otherwise None (use default)."""
    if os.environ.get("GROQ_API_KEY"):
        try:
            from adapters.groq_engine import GroqEngine
            return GroqEngine()
        except Exception:
            return None
    return None


def _import_debug_agent():
    _load_subagents_path()
    try:
        from supervisor_core.agents.debug_agent import DebugAgent  # type: ignore
        from supervisor_core.protocol.agent_types import AgentTask  # type: ignore
        return DebugAgent, AgentTask
    except ImportError as exc:
        raise ImportError(f"Could not import teammate DebugAgent: {exc}") from exc


def _import_test_agent():
    _load_subagents_path()
    try:
        from supervisor_core.agents.test_agent import TestAgent  # type: ignore
        from supervisor_core.protocol.agent_types import AgentTask  # type: ignore
        return TestAgent, AgentTask
    except ImportError as exc:
        raise ImportError(f"Could not import teammate TestAgent: {exc}") from exc


# ---------------------------------------------------------------------------
# Confidence mapping
# ---------------------------------------------------------------------------

_CONFIDENCE_MAP = {"high": 0.9, "medium": 0.6, "low": 0.3}


# ---------------------------------------------------------------------------
# Diff builder
# ---------------------------------------------------------------------------

def _find_enclosing_function(file_lines: list, target_line: int):
    """
    Parse file_lines as Python and return the ast.FunctionDef node (or None)
    whose lineno..end_lineno range contains target_line (1-based).
    Returns the shallowest (outermost) such node so that a top-level function
    is preferred over a nested one.
    """
    source = "".join(file_lines)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", None)
            if end is None:
                continue
            if start <= target_line <= end:
                # prefer the outermost (smallest range that still covers)
                if best is None or (end - start) > (best.end_lineno - best.lineno):
                    best = node
    return best


def _reindent_block(fix: str, target_indent_str: str) -> list:
    """
    Re-indent a multi-line block so its first line starts at target_indent_str.
    Relative indentation within the block is preserved.
    Returns a list of strings (no trailing newlines).
    """
    lines = fix.splitlines()
    if not lines:
        return []
    first_indent = len(lines[0]) - len(lines[0].lstrip())
    result = []
    for i, fl in enumerate(lines):
        if not fl.strip():
            result.append("")
        elif i == 0:
            result.append(target_indent_str + fl.lstrip())
        else:
            this_indent = len(fl) - len(fl.lstrip())
            extra = max(0, this_indent - first_indent)
            result.append(target_indent_str + " " * extra + fl.lstrip())
    return result


def _strip_non_code(lines: list) -> list:
    """Return lines with blank lines and comment-only lines removed."""
    result = []
    for l in lines:
        s = l.strip()
        if s and not s.startswith("#"):
            result.append(s)
    return result


def _build_diff(
    rel_path: str,
    file_lines: list,
    target_line: int,
    suggested_fix: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Build a unified diff. Returns (diff_str, error_message).

    Whole-function mode: if the first non-empty line of suggested_fix is
    "def <name>(" where <name> matches the function enclosing target_line,
    replace that entire function block with the re-indented suggested_fix.

    Single-line mode: replace only target_line (original behaviour).

    Post-build validations (both modes):
    - ast.parse the new content; reject if invalid Python.
    - Reject no-op: if code lines (non-blank, non-comment) are unchanged.
    """
    fix = suggested_fix.strip("\n")

    # Validation: empty
    if not fix.strip():
        return None, "suggestedFix is empty."

    fix_lines_raw = fix.splitlines()
    non_empty_fix = [l for l in fix_lines_raw if l.strip()]

    # Validation: comment-only
    if non_empty_fix and all(l.strip().startswith("#") for l in non_empty_fix):
        return None, "suggestedFix contains only comment lines."

    # Detect whole-function mode
    first_code_line = next((l.strip() for l in fix_lines_raw if l.strip()), "")
    enclosing_fn = _find_enclosing_function(file_lines, target_line)
    whole_fn_mode = (
        enclosing_fn is not None
        and first_code_line.startswith(f"def {enclosing_fn.name}(")
    )

    orig_line = file_lines[target_line - 1]

    if whole_fn_mode:
        # Find the original function's indentation (its def line)
        fn_def_line = file_lines[enclosing_fn.lineno - 1]
        fn_indent_str = fn_def_line[: len(fn_def_line) - len(fn_def_line.lstrip())]
        fn_start = enclosing_fn.lineno - 1          # 0-based
        fn_end   = enclosing_fn.end_lineno           # 0-based exclusive

        reindented = _reindent_block(fix, fn_indent_str)
        new_lines = (
            file_lines[:fn_start]
            + [(l if l.endswith("\n") else l + "\n") for l in reindented]
            + file_lines[fn_end:]
        )
    else:
        # Single-line mode
        orig_indent = len(orig_line) - len(orig_line.lstrip())
        orig_indent_str = orig_line[:orig_indent]

        # Validation: identical after strip (single-line only)
        if fix.strip() == orig_line.strip():
            return None, "suggestedFix is identical to the original line after stripping."

        reindented = _reindent_block(fix, orig_indent_str)
        new_lines = list(file_lines)
        new_lines[target_line - 1 : target_line] = [
            (l if l.endswith("\n") else l + "\n") for l in reindented
        ]

    # Validation: ast.parse the new content
    new_source = "".join(new_lines)
    try:
        ast.parse(new_source)
    except SyntaxError:
        return None, "suggested fix is not valid Python"

    # Validation: no-op check (compare code lines ignoring blanks and comments)
    orig_code = _strip_non_code(file_lines)
    new_code  = _strip_non_code(new_lines)
    if orig_code == new_code:
        return None, "suggested fix makes no code change"

    diff_str = "".join(difflib.unified_diff(
        file_lines,
        new_lines,
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
    ))

    if not diff_str:
        return None, "suggestedFix produces no changes."

    if not diff_str.endswith("\n"):
        diff_str += "\n"

    # Validate: diff only touches rel_path
    for dl in diff_str.splitlines():
        if dl.startswith("--- ") or dl.startswith("+++ "):
            path_in_diff = dl[4:].strip()
            if path_in_diff not in (f"a/{rel_path}", f"b/{rel_path}"):
                return None, f"Diff unexpectedly touches file: {path_in_diff}"

    return diff_str, None


# ---------------------------------------------------------------------------
# NancyDebugAdapter
# ---------------------------------------------------------------------------

class NancyDebugAdapter:
    """Adapter for the teammate's DebugAgent. AGENT_MODE=real."""

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        DebugAgent, AgentTask = _import_debug_agent()

        loc = locate(inp.repo_path, inp.bug_report)
        if loc is None:
            raise ValueError(
                "locator could not find a matching function for this bug report."
            )
        rel_path, target_line = loc
        abs_path = str(Path(inp.repo_path) / rel_path)

        try:
            file_text = Path(abs_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Cannot read {abs_path}: {exc}") from exc

        file_lines = file_text.splitlines(keepends=True)
        selected_code = file_lines[target_line - 1] if file_lines else ""

        task = AgentTask(
            id=uuid.uuid4().hex,
            type="debug",
            filePath=abs_path,
            line=target_line,
            selectedCode=selected_code,
            surroundingCode=file_text,
            language="python",
            instruction=inp.bug_report,
            source="supervisor",
        )

        started = datetime.now(timezone.utc)
        engine = _get_engine()
        agent = DebugAgent(engine=engine) if engine is not None else DebugAgent()
        result = await asyncio.to_thread(agent.execute, task)
        finished = datetime.now(timezone.utc)

        # Map timestamps
        ts_started = datetime.fromtimestamp(task.timestamp, tz=timezone.utc)

        if result.status != "completed" or result.debugData is None:
            error_text = result.error or "DebugAgent returned non-completed status."
            return SubAgentResult(
                agent="debug",
                status="failed",
                summary=f"debug failed: {error_text}",
                findings=[],
                proposed_patch=None,
                evidence=[],
                error=error_text,
                started_at=ts_started,
                finished_at=finished,
            )

        payload = result.debugData
        confidence_val = _CONFIDENCE_MAP.get(payload.confidence, 0.6)

        # Build diff
        patch_str, diff_error = _build_diff(
            rel_path, file_lines, target_line, payload.suggestedFix
        )
        if diff_error:
            return SubAgentResult(
                agent="debug",
                status="failed",
                summary=f"debug patch invalid: {diff_error}",
                findings=[],
                proposed_patch=None,
                evidence=[],
                error=diff_error,
                started_at=ts_started,
                finished_at=finished,
            )

        findings = [Finding(
            file=rel_path,
            claim=payload.detectedIssue,
            confidence=confidence_val,
            evidence_ids=["nancy-debug-ev-1", "nancy-debug-ev-2"],
            line=target_line,
        )]

        evidence = [
            EvidenceItem(
                id="nancy-debug-ev-1",
                type="reasoning",
                source="debug",
                content=f"{payload.evidenceReasoning}\n{payload.justification}",
            ),
            EvidenceItem(
                id="nancy-debug-ev-2",
                type="code_ref",
                source="debug",
                content=f"{rel_path}:{target_line}: {selected_code.rstrip()}",
            ),
        ]

        return SubAgentResult(
            agent="debug",
            status="ok",
            summary=result.summary or payload.detectedIssue,
            findings=findings,
            proposed_patch=patch_str,
            evidence=evidence,
            error=None,
            started_at=ts_started,
            finished_at=finished,
        )


# ---------------------------------------------------------------------------
# NancyTestAdapter
# ---------------------------------------------------------------------------

class NancyTestAdapter:
    """Adapter for the teammate's TestAgent. AGENT_MODE=real."""

    async def run(self, inp: SubAgentInput) -> SubAgentResult:
        TestAgent, AgentTask = _import_test_agent()

        loc = locate(inp.repo_path, inp.bug_report)
        if loc is None:
            raise ValueError(
                "locator could not find a matching function for this bug report."
            )
        rel_path, target_line = loc
        abs_path = str(Path(inp.repo_path) / rel_path)

        try:
            file_text = Path(abs_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Cannot read {abs_path}: {exc}") from exc

        file_lines = file_text.splitlines(keepends=True)
        selected_code = file_lines[target_line - 1] if file_lines else ""

        task = AgentTask(
            id=uuid.uuid4().hex,
            type="test",
            filePath=abs_path,
            line=target_line,
            selectedCode=selected_code,
            surroundingCode=file_text,
            language="python",
            instruction=inp.bug_report,
            source="supervisor",
        )

        started = datetime.now(timezone.utc)
        engine = _get_engine()
        agent = TestAgent(engine=engine) if engine is not None else TestAgent()
        result = await asyncio.to_thread(agent.execute, task)
        finished = datetime.now(timezone.utc)

        ts_started = datetime.fromtimestamp(task.timestamp, tz=timezone.utc)

        if result.status != "completed" or result.testData is None:
            error_text = result.error or "TestAgent returned non-completed status."
            return SubAgentResult(
                agent="test",
                status="failed",
                summary=f"test failed: {error_text}",
                findings=[],
                proposed_patch=None,
                evidence=[],
                error=error_text,
                started_at=ts_started,
                finished_at=finished,
            )

        payload = result.testData

        findings = [Finding(
            file=rel_path,
            claim=payload.whatShouldBeTested,
            confidence=0.8,
            evidence_ids=["nancy-test-ev-1", "nancy-test-ev-2"],
            line=target_line,
        )]

        evidence = [
            EvidenceItem(
                id="nancy-test-ev-1",
                type="reasoning",
                source="test",
                content=payload.expectedBehavior,
            ),
            EvidenceItem(
                id="nancy-test-ev-2",
                type="reasoning",
                source="test",
                content=f"Generated test (not executed): {payload.generatedTestCode or ''}",
            ),
        ]

        return SubAgentResult(
            agent="test",
            status="ok",
            summary=result.summary or payload.whatShouldBeTested,
            findings=findings,
            proposed_patch=None,
            evidence=evidence,
            error=None,
            started_at=ts_started,
            finished_at=finished,
        )
