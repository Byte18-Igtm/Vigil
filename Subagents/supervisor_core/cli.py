import argparse
import json
import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisor_core.supervisor.supervisor_agent import SupervisorAgent


def main():
    parser = argparse.ArgumentParser(description="Supervisor Agent CLI")
    parser.add_argument("agent", choices=["explain", "debug", "test"], help="Action to request from Supervisor")
    parser.add_argument("file", help="Path to code file")
    parser.add_argument("line", type=int, help="Target line number (1-based)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    target_idx = args.line - 1
    selected_code = lines[target_idx].strip() if 0 <= target_idx < len(lines) else ""
    start_ctx = max(0, target_idx - 10)
    end_ctx = min(len(lines), target_idx + 10)
    surrounding_code = "".join(lines[start_ctx:end_ctx])

    supervisor = SupervisorAgent()
    supervisor.register_marker(args.file, args.line)

    print(f"\n[USER REQUEST] Line {args.line} -> {args.agent.capitalize()}")
    print("=" * 60)

    result = supervisor.dispatch_request(
        agent_type=args.agent,
        file_path=os.path.abspath(args.file),
        line=args.line,
        selected_code=selected_code,
        surrounding_code=surrounding_code,
        language="python" if args.file.endswith(".py") else "javascript"
    )

    print(f"\n[SUPERVISOR VERBAL RESPONSE]")
    print(result.supervisorVerdict)
    print("\n[WORKER RESULT DETAILS]")
    print(result.details)
    print("\n[SUPERVISOR TIMELINE]")
    for ev in supervisor.get_event_history():
        print(f"[{time_format(ev.timestamp)}] {ev.message} (status: {ev.status})")


def time_format(epoch_seconds: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(epoch_seconds).strftime("%H:%M:%S")


if __name__ == "__main__":
    main()
