#!/usr/bin/env bash
# Supervisor/scripts/smoke_e2e.sh
# End-to-end smoke test (stub mode, no key needed).
# Usage: bash Supervisor/scripts/smoke_e2e.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SUPERVISOR_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SUBAGENTS_DIR="$(cd "$SUPERVISOR_DIR/../Subagents" && pwd)"
PYTHON="$SUPERVISOR_DIR/.venv/bin/python"
API_URL="http://127.0.0.1:8000"
LOG_FILE="$SUPERVISOR_DIR/.smoke_api.log"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

cleanup() {
  if [ -n "${API_PID:-}" ] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
    echo "Server stopped (pid $API_PID)."
  fi
}
trap cleanup EXIT

http_get() {
  curl -sf "$API_URL$1"
}

# http_post: prints response body; on HTTP error prints "FAIL: … status=N body=…" and exits.
http_post() {
  local path="$1"; local body="$2"
  local tmpfile; tmpfile=$(mktemp)
  local http_code
  http_code=$(curl -s -o "$tmpfile" -w "%{http_code}" \
    -X POST -H "Content-Type: application/json" -d "$body" "$API_URL$path")
  local resp; resp=$(cat "$tmpfile"); rm -f "$tmpfile"
  if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 300 ]; then
    echo "FAIL: POST $path returned status=$http_code body=$resp" >&2
    exit 1
  fi
  echo "$resp"
}

# ---------------------------------------------------------------------------
# Step 1: Recreate demo repo
# ---------------------------------------------------------------------------
echo "=== Step 1: Recreating demo repo ==="
PATCHPERMIT_SUBAGENTS_PATH="$SUBAGENTS_DIR" \
  "$PYTHON" "$SCRIPT_DIR/setup_demo_repo.py" --force
DEMO_REPO="$SUPERVISOR_DIR/demo_target"
echo "Demo repo: $DEMO_REPO"

# ---------------------------------------------------------------------------
# Step 2: Start API server in background
# ---------------------------------------------------------------------------
echo "=== Step 2: Starting API server ==="
PATCHPERMIT_AGENT_MODE=stub \
PATCHPERMIT_ALLOWED_REPO_ROOT="$SUPERVISOR_DIR" \
PATCHPERMIT_SUBAGENTS_PATH="$SUBAGENTS_DIR" \
  "$PYTHON" -m uvicorn api:app --host 127.0.0.1 --port 8000 \
    >"$LOG_FILE" 2>&1 &
API_PID=$!
echo "API pid: $API_PID  log: $LOG_FILE"

# Wait up to 15s for health
READY=0
for i in $(seq 1 30); do
  sleep 0.5
  if http_get /health >/dev/null 2>&1; then
    READY=1
    break
  fi
done
[ "$READY" -eq 1 ] || fail "API did not become healthy within 15s"
HEALTH=$(http_get /health)
echo "Health: $HEALTH"
pass "API healthy"

# ---------------------------------------------------------------------------
# Session A: create → investigate → approve
# ---------------------------------------------------------------------------
echo ""
echo "=== Session A: approve flow ==="

SESS_A=$(http_post /sessions \
  "{\"repo_path\":\"$DEMO_REPO\",\"bug_report\":\"average() returns wrong result\",\"consent_confirmed\":true}")
SID_A=$(echo "$SESS_A" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "session_id: $SID_A"

REPORT_A=$(http_post "/sessions/$SID_A/investigate" '{}')
STATE_A=$(echo "$REPORT_A" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['state'])")
HASH_A=$(echo "$REPORT_A" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['patch_hash'])")

[ "$STATE_A" = "AWAITING_APPROVAL" ] || fail "Session A: expected AWAITING_APPROVAL, got $STATE_A"
[ -n "$HASH_A" ] && [ "$HASH_A" != "None" ] || fail "Session A: patch_hash is missing or None"
pass "Session A: state=AWAITING_APPROVAL, patch_hash present ($HASH_A)"

FINAL_A=$(http_post "/sessions/$SID_A/decision" \
  "{\"decision\":\"approve\",\"patch_hash\":\"$HASH_A\",\"approver\":\"smoke-test\"}")
FINAL_STATE_A=$(echo "$FINAL_A" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['state'])")
TEST_RAN=$(echo "$FINAL_A" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('test_result',{}).get('ran',''))")
TEST_PASSED=$(echo "$FINAL_A" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('test_result',{}).get('passed',''))")

[ "$FINAL_STATE_A" = "COMPLETED" ] || fail "Session A: expected COMPLETED, got $FINAL_STATE_A"
[ "$TEST_RAN" = "True" ] || fail "Session A: test_result.ran is not True (got '$TEST_RAN')"
[ "$TEST_PASSED" = "True" ] || fail "Session A: test_result.passed is not True (got '$TEST_PASSED')"
pass "Session A: COMPLETED, tests ran and passed"

# ---------------------------------------------------------------------------
# Session B: recreate demo repo, then create → investigate → reject
# ---------------------------------------------------------------------------
echo ""
echo "=== Session B: recreating demo repo ==="
PATCHPERMIT_SUBAGENTS_PATH="$SUBAGENTS_DIR" \
  "$PYTHON" "$SCRIPT_DIR/setup_demo_repo.py" --force
echo "Demo repo reset."

echo "=== Session B: reject flow ==="

SESS_B=$(http_post /sessions \
  "{\"repo_path\":\"$DEMO_REPO\",\"bug_report\":\"average() returns wrong result\",\"consent_confirmed\":true}")
SID_B=$(echo "$SESS_B" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "session_id: $SID_B"

REPORT_B=$(http_post "/sessions/$SID_B/investigate" '{}')
HASH_B=$(echo "$REPORT_B" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['patch_hash'])")

FINAL_B=$(http_post "/sessions/$SID_B/decision" \
  "{\"decision\":\"reject\",\"patch_hash\":\"$HASH_B\",\"approver\":\"smoke-test\"}")
FINAL_STATE_B=$(echo "$FINAL_B" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['state'])")

[ "$FINAL_STATE_B" = "REJECTED" ] || fail "Session B: expected REJECTED, got $FINAL_STATE_B"
pass "Session B: REJECTED"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "==============================="
echo "Smoke test PASSED (all assertions)"
echo "==============================="
