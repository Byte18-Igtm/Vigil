from __future__ import annotations

# STUB: Understanding step
# Owner: TBD (see STUBS.md — "Open teammate decisions")
# Contract: receives repo_path and bug_report, returns a plain-text summary
# of the repository structure relevant to the bug report.
# Replace StubUnderstanding with a real implementation when the owner delivers it.

from typing import Protocol


class UnderstandingProvider(Protocol):
    async def summarise(self, repo_path: str, bug_report: str) -> str:
        ...


class StubUnderstanding:  # STUB
    """Returns a fixed summary sufficient for the demo scenario."""

    async def summarise(self, repo_path: str, bug_report: str) -> str:
        return (
            "Repository contains a Python package 'buggy_calc' with a single "
            "module calc.py. The average() function at line 1 uses floor "
            "division (//) on line 2, which truncates fractional results. "
            "A pytest suite in tests/test_calc.py asserts average([1,2,3,4]) "
            "== 2.5 and currently fails."
        )
