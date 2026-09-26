#!/usr/bin/env python
"""Start the PatchPermit Supervisor API with uvicorn."""
from __future__ import annotations

import os
import sys

# Ensure the Supervisor package directory is on sys.path when launched from anywhere
_SUPERVISOR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SUPERVISOR_DIR not in sys.path:
    sys.path.insert(0, _SUPERVISOR_DIR)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        workers=1,
        app_dir=_SUPERVISOR_DIR,
    )
