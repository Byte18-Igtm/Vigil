from __future__ import annotations

from typing import Callable, List, Optional

from models import SupervisorReport, TestRunResult
from redaction import redact


# ---------------------------------------------------------------------------
# Optional LLM / custom explanation provider hook
# ---------------------------------------------------------------------------

_explanation_provider: Optional[Callable[[str], str]] = None


def register_explanation_provider(fn: Callable[[str], str]) -> None:
    """Register an optional explanation generator.
    fn receives the template text and must return a non-empty plain string.
    Falls back to template if fn raises, returns a non-str, or returns
    an empty/whitespace-only string."""
    global _explanation_provider
    _explanation_provider = fn


def unregister_explanation_provider() -> None:
    """Remove any registered explanation provider."""
    global _explanation_provider
    _explanation_provider = None


# ---------------------------------------------------------------------------
# Deterministic template
# ---------------------------------------------------------------------------

def _render_template(report: SupervisorReport) -> str:
    agent_lines = "\n".join(
        f"  - {e.agent}: {e.status}"
        + (f" ({e.error})" if e.error else "")
        for e in report.agent_statuses
    )
    patch_line = (
        f"Proposed patch (hash: {report.patch_hash[:12]}...):"
        if report.patch and report.patch_hash
        else "No patch proposed."
    )
    confidence_pct = f"{report.confidence * 100:.0f}%"
    limitations = (
        "\n".join(f"  - {lim}" for lim in report.limitations)
        if report.limitations
        else "  None noted."
    )
    conflicts = (
        "\n".join(
            f"  - {c.description} (resolution: {c.resolution})"
            for c in report.conflicts
        )
        if report.conflicts
        else "  None."
    )
    selection = report.selection_reason or "N/A"
    root_cause = report.root_cause if report.root_cause else "Unknown"

    return (
        f"Bug summary: {root_cause}\n\n"
        f"Agent investigation results:\n{agent_lines}\n\n"
        f"Patch selection: {selection}\n"
        f"{patch_line}\n\n"
        f"Confidence: {confidence_pct}\n\n"
        f"Conflicts:\n{conflicts}\n\n"
        f"Limitations:\n{limitations}"
    )


def build_explanation(report: SupervisorReport) -> str:
    """Return the explanation string, redacted.
    Uses the registered provider if set and usable; otherwise the template."""
    template_text = _render_template(report)
    result = template_text
    if _explanation_provider is not None:
        try:
            provider_output = _explanation_provider(template_text)
            if isinstance(provider_output, str) and provider_output.strip():
                result = provider_output
            # else: empty/whitespace or wrong type → fall back to template
        except Exception:
            pass  # provider failure → template
    return redact(result)


# ---------------------------------------------------------------------------
# Chat summary renderer
# ---------------------------------------------------------------------------

_IN_PROGRESS_STATES = {
    "CREATED", "UNDERSTANDING", "INVESTIGATING",
    "AGGREGATING", "APPROVED", "APPLYING", "TESTING",
}


def render_chat_summary(report: SupervisorReport) -> str:
    """
    Return a concise, honest plain-text chat message summarising the outcome.

    Outcome is determined from TestRunResult, never from state name:
    - tr is None or not tr.ran  → "Tests not run."
    - tr.ran and tr.passed      → "Tests passed."  (only when state == COMPLETED)
    - tr.ran and not tr.passed  → "Tests failed."

    If state == COMPLETED but tr is not ran+passed, a disagreement warning
    is printed and the word "passed" is never used.

    If state is something other than COMPLETED but tr.ran and tr.passed,
    a disagreement warning is printed (tests did run but state is wrong).

    The returned string is fully redacted.
    """
    state = report.state
    tr: Optional[TestRunResult] = report.test_result
    lines: List[str] = []

    lines.append(f"Session {report.session_id} — {state}")
    lines.append("")

    # --- Terminal states without patch/test ---
    if state == "REJECTED":
        lines.append("Decision: REJECTED. No patch was applied.")
        lines.append("Tests were not run.")
        if report.explanation:
            lines.append(f"\nContext:\n{report.explanation}")
        return redact("\n".join(lines))

    if state == "NO_PATCH":
        lines.append("No patch was proposed.")
        lines.append("Tests were not run.")
        if report.failure_reason:
            lines.append(f"Reason: {report.failure_reason}")
        lines.append(f"\nExplanation:\n{report.explanation}")
        return redact("\n".join(lines))

    if state == "FAILED":
        lines.append("Session failed.")
        lines.append("Tests were not run.")
        if report.failure_reason:
            lines.append(f"Reason: {report.failure_reason}")
        lines.append(f"\nExplanation:\n{report.explanation}")
        return redact("\n".join(lines))

    # --- Awaiting approval ---
    if state == "AWAITING_APPROVAL":
        lines.append("Awaiting your approval. Nothing has been applied.")
        if report.patch_hash:
            lines.append(f"Patch hash: {report.patch_hash[:12]}...")
        if report.selection_reason:
            lines.append(f"Selection: {report.selection_reason}")
        if report.root_cause:
            lines.append(f"Root cause: {report.root_cause}")
        lines.append(f"\nExplanation:\n{report.explanation}")
        return redact("\n".join(lines))

    # --- In-progress states ---
    if state in _IN_PROGRESS_STATES:
        lines.append(f"In progress: {state}.")
        return redact("\n".join(lines))

    # --- States with test results (COMPLETED, TESTS_FAILED, and any unexpected) ---
    if report.patch_hash:
        lines.append(f"Patch hash: {report.patch_hash[:12]}...")
    if report.selection_reason:
        lines.append(f"Selection: {report.selection_reason}")
    if report.root_cause:
        lines.append(f"Root cause: {report.root_cause}")
    if report.branch:
        lines.append(f"Branch: {report.branch}")
    lines.append("")

    # Determine test outcome from TestRunResult only
    if tr is None or not tr.ran:
        if state == "COMPLETED":
            lines.append(
                "Warning: state and test result disagree — not claiming success."
            )
        lines.append("Tests not run.")
        if tr is not None and tr.output_tail:
            lines.append(f"Note: {tr.output_tail}")
    elif tr.ran and tr.passed:
        if state != "COMPLETED":
            lines.append(
                "Warning: state and test result disagree — not claiming success."
            )
        else:
            lines.append("Tests passed.")
            if tr.command:
                lines.append(f"  Command: {tr.command}")
            if tr.duration is not None:
                lines.append(f"  Duration: {tr.duration:.1f}s")
    else:  # tr.ran and not tr.passed
        if state == "COMPLETED":
            lines.append(
                "Warning: state and test result disagree — not claiming success."
            )
        lines.append("Tests failed.")
        if tr.command:
            lines.append(f"  Command: {tr.command}")
        if tr.exit_code is not None:
            lines.append(f"  Exit code: {tr.exit_code}")
        if tr.output_tail:
            lines.append(f"  Output (tail):\n{tr.output_tail}")

    lines.append("")
    lines.append(f"Explanation:\n{report.explanation}")

    if report.conflicts:
        lines.append("\nConflicts:")
        for c in report.conflicts:
            lines.append(f"  - {c.description} [{c.resolution}]")

    if report.limitations:
        lines.append("\nLimitations:")
        for lim in report.limitations:
            lines.append(f"  - {lim}")

    return redact("\n".join(lines))
