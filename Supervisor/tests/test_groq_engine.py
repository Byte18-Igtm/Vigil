from __future__ import annotations

"""Tests for GroqEngine — no network, no real key."""

import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Skip guard: needs PATCHPERMIT_SUBAGENTS_PATH to import the base class
# ---------------------------------------------------------------------------

import os
SUBAGENTS_PATH = os.environ.get("PATCHPERMIT_SUBAGENTS_PATH", "")
pytestmark = pytest.mark.skipif(
    not SUBAGENTS_PATH,
    reason="PATCHPERMIT_SUBAGENTS_PATH is not set — groq_engine tests skipped",
)


def _make_engine(monkeypatch, api_key="test-key-abc", model="llama3-70b-8192"):
    monkeypatch.setenv("GROQ_API_KEY", api_key)
    monkeypatch.setenv("PATCHPERMIT_GROQ_MODEL", model)
    from adapters.groq_engine import GroqEngine
    return GroqEngine()


class TestGroqEngine:
    def test_bearer_header_used_key_not_in_url(self, monkeypatch):
        engine = _make_engine(monkeypatch)
        captured = {}

        def fake_post(url, headers, json, timeout):
            captured["url"] = url
            captured["headers"] = headers
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": '{"result": 1}'}}]
            }
            return mock_resp

        with patch("requests.post", side_effect=fake_post):
            result = engine._call_gemini_json("prompt", "system")

        assert result == {"result": 1}
        # Key is in Authorization header, not in URL
        assert "Bearer test-key-abc" in captured["headers"]["Authorization"]
        assert "test-key-abc" not in captured["url"]

    def test_parsed_dict_returned(self, monkeypatch):
        engine = _make_engine(monkeypatch)
        payload = {"suggestedFix": "return x / y", "confidence": "high"}

        def fake_post(url, headers, json, timeout):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": json_module.dumps(payload)}}]
            }
            return mock_resp

        import json as json_module
        with patch("requests.post", side_effect=fake_post):
            result = engine._call_gemini_json("p", "s")
        assert result == payload

    def test_none_on_http_error(self, monkeypatch):
        engine = _make_engine(monkeypatch)

        def fake_post(url, headers, json, timeout):
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            return mock_resp

        with patch("requests.post", side_effect=fake_post):
            result = engine._call_gemini_json("p", "s")
        assert result is None

    def test_none_on_bad_json(self, monkeypatch):
        engine = _make_engine(monkeypatch)

        def fake_post(url, headers, json, timeout):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": "not json {"}}]
            }
            return mock_resp

        with patch("requests.post", side_effect=fake_post):
            result = engine._call_gemini_json("p", "s")
        assert result is None

    def test_none_on_network_error(self, monkeypatch):
        engine = _make_engine(monkeypatch)

        with patch("requests.post", side_effect=ConnectionError("timeout")):
            result = engine._call_gemini_json("p", "s")
        assert result is None

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.setenv("PATCHPERMIT_GROQ_MODEL", "llama3-70b-8192")
        from adapters.groq_engine import GroqEngine
        with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
            GroqEngine()

    def test_missing_model_raises(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "some-key")
        monkeypatch.delenv("PATCHPERMIT_GROQ_MODEL", raising=False)
        from adapters.groq_engine import GroqEngine
        with pytest.raises(EnvironmentError, match="PATCHPERMIT_GROQ_MODEL"):
            GroqEngine()
