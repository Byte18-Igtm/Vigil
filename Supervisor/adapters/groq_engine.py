from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional


def _load_subagents_path_for_groq() -> None:
    path = os.environ.get("PATCHPERMIT_SUBAGENTS_PATH", "")
    if not path:
        raise ImportError(
            "PATCHPERMIT_SUBAGENTS_PATH is not set. "
            "Set it to the absolute path of the Subagents directory."
        )
    if path not in sys.path:
        sys.path.append(path)


def _import_base_engine():
    _load_subagents_path_for_groq()
    try:
        from supervisor_core.llm.engine import CodeIntelligenceEngine  # type: ignore
        return CodeIntelligenceEngine
    except ImportError as exc:
        raise ImportError(f"Could not import CodeIntelligenceEngine: {exc}") from exc


class GroqEngine:
    """
    Drop-in replacement for CodeIntelligenceEngine that routes LLM calls
    through the Groq OpenAI-compatible API.

    Inherits dynamically from CodeIntelligenceEngine so prompt-building and
    payload parsing are reused; only _call_gemini_json is overridden.
    """

    def __new__(cls, *args, **kwargs):
        CodeIntelligenceEngine = _import_base_engine()
        dynamic_cls = type(
            "GroqEngine",
            (CodeIntelligenceEngine,),
            {
                "__init__": _groq_init,
                "_call_gemini_json": _call_gemini_json,
            },
        )
        instance = object.__new__(dynamic_cls)
        _groq_init(instance)
        return instance

    def __init__(self):
        # Actual init is _groq_init, installed on the dynamic class.
        pass


def _groq_init(self) -> None:
    """Instance __init__ installed on the dynamically created subclass."""
    super(type(self), self).__init__()

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is not set.")

    model = os.environ.get("PATCHPERMIT_GROQ_MODEL", "")
    if not model:
        raise EnvironmentError("PATCHPERMIT_GROQ_MODEL environment variable is not set.")

    self._groq_api_key = api_key
    self._groq_model = model
    # Signal to parent that AI credentials are present (takes the LLM branch)
    self.gemini_api_key = "groq-enabled"


def _call_gemini_json(
    self, prompt: str, system_instruction: str
) -> Optional[Dict[str, Any]]:
    """Override: POST to Groq's OpenAI-compatible endpoint. Key stays in header only."""
    import requests as _requests

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {self._groq_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": self._groq_model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    try:
        res = _requests.post(url, headers=headers, json=body, timeout=12)
        if res.status_code == 200:
            data = res.json()
            raw_text = data["choices"][0]["message"]["content"]
            return json.loads(raw_text)
        return None
    except Exception:
        return None
