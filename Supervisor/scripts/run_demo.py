from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

import supervisor as sv
from explanation import render_chat_summary
from models import ApprovalDecision
from aggregation import patch_hash as compute_patch_hash


def _print_report(report) -> None:
    print("\n" + "=" * 60)
    print(f"Session: {report.session_id}  State: {report.state}")
    print("=" * 60)
    print(f"\nExplanation:\n{report.explanation}")
    if report.patch:
        print(f"\nPatch (hash: {report.patch_hash}):\n{report.patch}")
    else:
        print("\nNo patch proposed.")
    if report.evidence:
        print("\nEvidence:")
        for e in report.evidence:
            print(f"  [{e.source}] {e.id}: {e.content}")
    print("\nAgent statuses:")
    for a in report.agent_statuses:
        status_line = f"  {a.agent}: {a.status}"
        if a.error:
            status_line += f" ({a.error})"
        print(status_line)
    if report.conflicts:
        print("\nConflicts:")
        for c in report.conflicts:
            print(f"  {c.description} [{c.resolution}]")
    if report.selection_reason:
        print(f"\nSelection reason: {report.selection_reason}")
    print("=" * 60)


async def _main(repo_path: str) -> None:
    repo = Path(repo_path)
    bug_report_path = repo / "bug_report.txt"
    if not bug_report_path.exists():
        print(f"Error: bug_report.txt not found in {repo}", file=sys.stderr)
        sys.exit(1)

    bug_report = bug_report_path.read_text(encoding="utf-8")
    print(f"Bug report loaded from {bug_report_path}")
    print(f"Repository: {repo}")

    session_id = await sv.create_session(
        repo_path=str(repo),
        bug_report=bug_report,
        consent_confirmed=True,
    )
    print(f"\nSession created: {session_id}")
    print("Running investigation (this may take a moment)...")

    report = await sv.run_investigation(session_id)
    _print_report(report)

    if report.state != "AWAITING_APPROVAL":
        print(f"\nFinal state: {report.state}")
        print(render_chat_summary(report))
        return

    print('\nType "approve" or "reject" and press Enter:')
    try:
        user_input = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return

    if user_input not in ("approve", "reject"):
        print(f"Unknown input {user_input!r}. Aborting.")
        return

    decision = ApprovalDecision(
        session_id=session_id,
        patch_hash=report.patch_hash,
        decision=user_input,
        approver="demo-user",
        timestamp=datetime.now(timezone.utc),
        comment=None,
    )

    print(f"\nSubmitting {user_input}...")
    final = await sv.submit_approval(decision)
    print(render_chat_summary(final))


def main():
    parser = argparse.ArgumentParser(description="PatchPermit demo CLI")
    parser.add_argument(
        "--repo", default="./demo_target",
        help="Path to the demo target repository (default: ./demo_target)",
    )
    args = parser.parse_args()
    asyncio.run(_main(args.repo))


if __name__ == "__main__":
    main()
