from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent.parent / "demo_repo_template"
DEFAULT_TARGET = Path(__file__).parent.parent / "demo_target"


def run(args, cwd):
    """Run a subprocess command, raise on non-zero exit."""
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Set up the PatchPermit demo target repository."
    )
    parser.add_argument(
        "--target", default=str(DEFAULT_TARGET),
        help="Path to create the demo repo (default: ./demo_target)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Remove and recreate the target if it already exists.",
    )
    args = parser.parse_args()

    target = Path(args.target)

    if target.exists():
        if args.force:
            marker = target / ".git" / "patchpermit-demo"
            if not marker.exists():
                print(
                    f"Error: {target} exists but is not a PatchPermit demo repo "
                    "(missing .git/patchpermit-demo marker). "
                    "Refusing to delete. Remove it manually if you are sure.",
                    file=sys.stderr,
                )
                sys.exit(1)
            shutil.rmtree(target)
        else:
            print(
                f"Error: target path already exists: {target}\n"
                "Use --force to overwrite.",
                file=sys.stderr,
            )
            sys.exit(1)

    shutil.copytree(
        TEMPLATE_DIR, target,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"),
    )
    print(f"Copied template to {target}")

    try:
        run(["git", "init"], cwd=target)
    except FileNotFoundError:
        shutil.rmtree(target)
        print(
            "Error: git is not installed or not on PATH. "
            "Please install git and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Write marker inside .git so --force can verify this is a demo repo
    marker = target / ".git" / "patchpermit-demo"
    marker.write_text("PatchPermit demo repo — safe to delete with --force\n")

    run(["git", "add", "."], cwd=target)
    run(
        [
            "git",
            "-c", "user.name=PatchPermit",
            "-c", "user.email=patchpermit@localhost",
            "commit", "-m", "Initial commit: buggy_calc with known bug",
        ],
        cwd=target,
    )
    print(f"Demo repo ready at: {target}")
    print("Note: add demo_target/ to .gitignore in the team repo.")


if __name__ == "__main__":
    main()
