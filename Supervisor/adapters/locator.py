from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Optional, Tuple


def locate(repo_path: str, bug_report: str) -> Optional[Tuple[str, int]]:
    """
    Scan *.py files under repo_path for a function named in bug_report.

    Identifiers are extracted by looking for patterns like  name(  or  name()
    in the bug_report text.

    Skips directories: .git, any dir whose name contains 'venv', and tests/.

    Target line = line number of the function's first body statement that is
    not a docstring (i.e. not a bare Expr(Constant/Str)).

    Returns (relative_file_path, line) or None.
    Deterministic: when several files match, the first by sorted path wins.
    """
    import re

    # Extract candidate function names from the bug report
    names = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', bug_report)
    if not names:
        return None
    # Preserve order, deduplicate
    seen = set()
    candidates = []
    for n in names:
        if n not in seen:
            seen.add(n)
            candidates.append(n)

    root = Path(repo_path)

    def _skip(dir_name: str) -> bool:
        return dir_name in {".git", "tests"} or "venv" in dir_name.lower()

    py_files = sorted(
        p for p in root.rglob("*.py")
        if not any(_skip(part) for part in p.relative_to(root).parts[:-1])
    )

    for func_name in candidates:
        for py_file in py_files:
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, OSError):
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name != func_name:
                    continue
                # Find first body statement that is not a docstring
                target_line = node.lineno  # fallback
                for stmt in node.body:
                    if (
                        isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, (ast.Constant, ast.Str))
                    ):
                        continue  # skip docstring
                    target_line = stmt.lineno
                    break
                rel = str(py_file.relative_to(root))
                return rel, target_line

    return None
