# STUBS.md — PatchPermit Supervisor Slice

This file lists every stub, open teammate decision, known limitation, and
optional feature that is not yet implemented.

---

## Stubs

Each item is marked `# STUB` in source code and must be replaced before
production use.

| Stub | File | What it does | What real code must provide |
|---|---|---|---|
| `StubUnderstanding` | `adapters/understanding.py` | Returns a fixed summary string for the demo bug | A real implementation that reads the repo and summarises relevant files |
| `StubDebugAgent` | `adapters/debug_agent.py` | Returns a hardcoded `SubAgentResult` with the `//`→`/` fix patch | Real debug agent producing `SubAgentResult` per contract below |
| `StubTestAgent` | `adapters/test_agent.py` | Returns a corroborating finding, no patch | Real test agent producing `SubAgentResult` per contract below |
| `StubMaintenanceAgent` | `adapters/maintenance_agent.py` | Returns a conflicting rename patch (higher confidence than debug) | Real maintenance agent producing `SubAgentResult` per contract below |
| `StubDebugAgentFailing` / `StubTestAgentFailing` / `StubMaintenanceAgentFailing` | respective adapter files | Raise `RuntimeError` immediately | N/A — test-only |
| `StubSlowAgent` | `adapters/fakes.py` | Sleeps for a configurable delay, then returns `ok` | N/A — test-only |
| `DebugAgentAdapter` / `TestAgentAdapter` / `MaintenanceAgentAdapter` | respective adapter files | Protocol stubs | Real adapter wrapping the teammate implementation |

### Sub-agent result contract

Every real sub-agent must return a `SubAgentResult` with:

```
agent:          "debug" | "test" | "maintenance"
status:         "ok" | "failed"   # supervisor assigns "timeout" / "skipped"
summary:        str
findings:       list of { file, line?, claim, confidence (0–1), evidence_ids }
proposed_patch: unified diff string or None
evidence:       list of { id, type, source, content }
error:          str or None
started_at:     datetime (UTC, timezone-aware)
finished_at:    datetime (UTC, timezone-aware)
```

**Important:**
- `repo_path` is **read-only** for agents. Agents return diffs only; they never
  write files, run git, or apply patches.
- `file` in findings must use the repo-relative path (e.g. `buggy_calc/calc.py`),
  matching the `a/` prefix in diff headers. Corroboration line-matching will fail
  if paths differ.
- Datetimes are `datetime` objects in-process; ISO-8601 only when serialised.

---

## Open teammate decisions

These must be agreed before the demo or real integration:

1. **Front-end transport** — currently direct Python function calls. Whether the
   front end needs an HTTP wrapper (FastAPI/Flask) is unresolved. The supervisor
   public API (`create_session`, `run_investigation`, `submit_approval`,
   `get_session_report`) is the interface to wrap.

2. **Sub-agent field names and confidence** — specifically whether `confidence`
   is always provided (0–1) or optional. An absent or zero confidence will fall
   through to the line-count and agent-order tiebreaks.

3. **Agent transport** — currently in-process async function calls. If agents
   run as separate services, each adapter must be updated to make HTTP/queue
   calls. The `asyncio.wait_for` timeout wrapper stays.

4. **Agent timeout** — default 30 s (`PATCHPERMIT_AGENT_TIMEOUT_SEC`).
   Confirm with sub-agent owners.

5. **Understanding step owner** — `StubUnderstanding` is a stub. The owner of
   this step must deliver a real implementation or confirm the stub is
   acceptable for the demo.

6. **LLM provider for explanation** — `ExplanationProvider` hook exists in
   `explanation.py`. No LLM SDK is committed. Provider, model, and credentials
   must be agreed. Until then, the deterministic template is used.

7. **Team Python version** — the venv is Python 3.9.6. All teammates must
   confirm compatibility.

8. **demo_target location** — `scripts/setup_demo_repo.py` creates `./demo_target`
   by default. Add `demo_target/` to `.gitignore` in the team repo. Do not commit
   the demo target.

---

## Voice output

Voice output is **optional and not implemented**. The `render_chat_summary`
function returns a plain-text string. A voice hook could read it aloud (e.g.
via `say` on macOS or a TTS API), but no such hook exists. It must never block
the flow.

---

## Known aggregation limitations

1. **New-file patches** (`--- /dev/null`) are not counted in `_touched_files`,
   so they will not show as overlapping with other patches. This does not affect
   the demo (the demo patch modifies an existing file).

2. **Removed content lines starting with `-- `** would be misread as a `---`
   file header by the diff parser. This is an edge case that does not arise in
   the demo.
