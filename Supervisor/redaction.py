from __future__ import annotations

import os
import re

# Patterns that don't depend on env vars
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")
_SK_RE = re.compile(r"sk-[A-Za-z0-9]{20,}")

# Matches any env var name containing these words (substring, case-insensitive)
_SECRET_NAME_RE = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", re.IGNORECASE)

# Generic NAME=value / NAME: value pattern for secret-looking keys not in os.environ.
# Requires the word to END in one of the secret keywords (e.g. api_key, access_token).
# Does NOT match "KeyError: 'x'" because "KeyError" ends in "error", not a keyword.
_GENERIC_SECRET_RE = re.compile(
    r"(?i)\b[A-Za-z0-9_.\-]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIALS?)\s*[=:]\s*\S+"
)


def redact(text: str) -> str:
    """
    Redact secrets from text. Reads os.environ at call time.

    Replaces:
      (a) The literal value of any env var whose name contains KEY, TOKEN,
          SECRET, PASSWORD, or CREDENTIAL (case-insensitive), for values of
          6+ characters, wherever that value appears in text.
      (b) NAME=value and NAME: value patterns for those env var names.
      (b2) Generic secret-looking key patterns not covered by env vars.
      (c) Bearer <token> and sk-<key> patterns.

    Never logs or returns original secret values.
    """
    result = text

    # (a) redact bare env var values (6+ chars) for secret-named vars
    for name, value in os.environ.items():
        if not _SECRET_NAME_RE.search(name):
            continue
        if len(value) >= 6:
            result = result.replace(value, "[REDACTED]")

    # (b) redact NAME=value and NAME: value patterns for env var names
    for name in os.environ:
        if not _SECRET_NAME_RE.search(name):
            continue
        result = re.sub(
            r"(?i)" + re.escape(name) + r"\s*[=:]\s*\S+",
            name + "=[REDACTED]",
            result,
        )

    # (b2) generic secret-looking key patterns not covered by env vars
    result = _GENERIC_SECRET_RE.sub(
        lambda m: m.group(0).split("=")[0].split(":")[0].strip() + "=[REDACTED]",
        result,
    )

    # (c) bearer tokens and sk- style keys
    result = _BEARER_RE.sub("Bearer [REDACTED]", result)
    result = _SK_RE.sub("sk-[REDACTED]", result)

    return result
