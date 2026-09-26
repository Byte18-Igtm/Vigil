from __future__ import annotations

import pytest

from explanation import (
    build_explanation,
    register_explanation_provider,
    render_chat_summary,
    unregister_explanation_provider,
)
from models import (
    AgentStatusEntry,
    ConflictRecord,
    EvidenceItem,
    SupervisorReport,
    TestRunResult,
)
from redaction import redact


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_report(**kwargs) -> SupervisorReport:
    defaults = dict(
        session_id="sess-001",
        state="COMPLETED",
        explanation="The average function used // instead of /.",
        root_cause="Floor division instead of float division",
        patch="--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n ...",
        patch_hash="abc123def456" + "0" * 52,  # 64-char hex
        evidence=[],
        agent_statuses=[AgentStatusEntry(agent="debug", status="ok", error=None)],
        conflicts=[],
        confidence=0.7,
        limitations=[],
        patch_source_agents=["debug"],
        selection_reason="debug patch chosen: corroborated by test agent",
        failure_reason=None,
        branch="patchpermit/sess0001",
        test_result=None,
    )
    defaults.update(kwargs)
    return SupervisorReport(**defaults)


def _tr(ran: bool, passed: bool, exit_code: int = 0,
        command: str = "pytest -q", output_tail: str = "",
        duration: float = 1.0) -> TestRunResult:
    return TestRunResult(
        ran=ran,
        passed=passed,
        command=command,
        exit_code=exit_code if ran else None,
        output_tail=output_tail,
        duration=duration if ran else None,
    )


@pytest.fixture(autouse=True)
def _reset_provider():
    """Ensure the provider is unregistered before and after every test."""
    unregister_explanation_provider()
    yield
    unregister_explanation_provider()


# ---------------------------------------------------------------------------
# Direct redact() tests
# ---------------------------------------------------------------------------

class TestRedactDirect:
    def test_api_key_pattern_redacted(self):
        result = redact("api_key: xyz123abc")
        assert "xyz123abc" not in result
        assert "[REDACTED]" in result

    def test_bearer_token_redacted(self):
        result = redact("Authorization: Bearer " + "a" * 25)
        assert "a" * 25 not in result
        assert "[REDACTED]" in result

    def test_sk_key_redacted(self):
        result = redact("sk-" + "a" * 24)
        assert "a" * 24 not in result
        assert "[REDACTED]" in result

    def test_key_error_not_redacted(self):
        result = redact("KeyError: 'x'")
        assert result == "KeyError: 'x'"

    def test_normal_assertion_unchanged(self):
        result = redact("assert 2 == 2.5")
        assert result == "assert 2 == 2.5"

    def test_bare_env_value_redacted_with_underscore_name(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "zzzsecretvalue999")
        result = redact("the value zzzsecretvalue999 is here")
        assert "zzzsecretvalue999" not in result
        assert "[REDACTED]" in result


# ---------------------------------------------------------------------------
# Test outcome wording
# ---------------------------------------------------------------------------

class TestChatSummaryOutcome:
    def test_completed_ran_passed(self):
        r = _base_report(state="COMPLETED", test_result=_tr(True, True))
        s = render_chat_summary(r)
        assert "Tests passed." in s
        assert "not run" not in s.lower()

    def test_tests_failed_ran_not_passed(self):
        r = _base_report(
            state="TESTS_FAILED",
            test_result=_tr(True, False, exit_code=1, output_tail="FAILED test_calc.py"),
        )
        s = render_chat_summary(r)
        assert "Tests failed." in s
        assert "Exit code: 1" in s
        assert "tests passed" not in s.lower()

    def test_ran_false_contains_not_run(self):
        r = _base_report(state="TESTS_FAILED", test_result=_tr(False, False))
        s = render_chat_summary(r)
        assert "not run" in s.lower()
        assert "tests passed" not in s.lower()

    def test_completed_ran_not_passed_disagreement_warning(self):
        """COMPLETED state but ran=True, passed=False → warning, no 'passed'."""
        r = _base_report(
            state="COMPLETED",
            test_result=_tr(True, False, exit_code=1),
        )
        s = render_chat_summary(r)
        assert "disagree" in s.lower()
        assert "tests passed" not in s.lower()

    def test_awaiting_approval_nothing_applied(self):
        r = _base_report(state="AWAITING_APPROVAL", test_result=None)
        s = render_chat_summary(r)
        assert "Nothing has been applied" in s
        assert "tests passed" not in s.lower()
        # "not run" should NOT appear for AWAITING_APPROVAL (tests haven't started)
        assert "not run" not in s.lower()

    def test_rejected_contains_not_run(self):
        r = _base_report(state="REJECTED", test_result=None)
        s = render_chat_summary(r)
        assert "not run" in s.lower()

    def test_no_patch_contains_not_run(self):
        r = _base_report(
            state="NO_PATCH", patch=None, patch_hash=None,
            test_result=None, failure_reason="No usable patch.",
        )
        s = render_chat_summary(r)
        assert "not run" in s.lower()

    def test_failed_state_contains_not_run(self):
        r = _base_report(
            state="FAILED", test_result=None,
            failure_reason="Agent crashed.",
        )
        s = render_chat_summary(r)
        assert "not run" in s.lower()
        assert "Session failed." in s

    def test_tests_failed_ran_passed_inconsistent(self):
        """TESTS_FAILED state but ran=True, passed=True → warning, no 'tests passed', no 'not run'."""
        r = _base_report(
            state="TESTS_FAILED",
            test_result=_tr(True, True),
        )
        s = render_chat_summary(r)
        assert "disagree" in s.lower()
        assert "tests passed" not in s.lower()
        assert "not run" not in s.lower()


# ---------------------------------------------------------------------------
# Redaction via render_chat_summary / build_explanation
# ---------------------------------------------------------------------------

class TestRedaction:
    def test_secret_env_var_value_redacted_in_output_tail(self, monkeypatch):
        monkeypatch.setenv("PATCHPERMIT_TEST_TOKEN", "abc123supersecret")
        r = _base_report(
            state="TESTS_FAILED",
            test_result=_tr(
                True, False, exit_code=1,
                output_tail="token=abc123supersecret in logs",
            ),
        )
        s = render_chat_summary(r)
        assert "abc123supersecret" not in s
        assert "[REDACTED]" in s

    def test_secret_env_var_value_redacted_in_agent_error(self, monkeypatch):
        monkeypatch.setenv("PATCHPERMIT_TEST_TOKEN", "abc123supersecret")
        r = _base_report(
            state="FAILED",
            failure_reason="Agent error: abc123supersecret revealed",
            agent_statuses=[
                AgentStatusEntry(
                    agent="debug", status="failed",
                    error="token abc123supersecret leaked",
                )
            ],
        )
        explanation = build_explanation(r)
        summary = render_chat_summary(r)
        assert "abc123supersecret" not in explanation
        assert "abc123supersecret" not in summary
        assert "[REDACTED]" in explanation or "[REDACTED]" in summary

    def test_normal_text_unchanged(self, monkeypatch):
        monkeypatch.delenv("PATCHPERMIT_TEST_TOKEN", raising=False)
        r = _base_report(
            state="TESTS_FAILED",
            test_result=_tr(
                True, False, exit_code=1,
                output_tail="assert 2 == 2.5",
            ),
        )
        s = render_chat_summary(r)
        assert "assert 2 == 2.5" in s


# ---------------------------------------------------------------------------
# Explanation provider hook
# ---------------------------------------------------------------------------

class TestExplanationProvider:
    def test_provider_that_raises_falls_back_to_template(self):
        def bad_provider(_text: str) -> str:
            raise RuntimeError("LLM unavailable")

        register_explanation_provider(bad_provider)
        r = _base_report()
        result = build_explanation(r)
        assert "Floor division" in result or "Bug summary" in result

    def test_provider_returning_empty_string_falls_back_to_template(self):
        register_explanation_provider(lambda _: "")
        r = _base_report()
        result = build_explanation(r)
        assert "Bug summary" in result

    def test_provider_output_containing_secret_is_redacted(self, monkeypatch):
        monkeypatch.setenv("PATCHPERMIT_TEST_TOKEN", "abc123supersecret")
        register_explanation_provider(lambda _: "Here is abc123supersecret exposed")
        r = _base_report()
        result = build_explanation(r)
        assert "abc123supersecret" not in result
        assert "[REDACTED]" in result
