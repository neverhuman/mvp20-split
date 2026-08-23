#!/usr/bin/env bash
# Sandbox harness: runs the REAL launcher against a throwaway ROOT, a fake
# agent binary, and a dead ssh, so gate/counter/classifier/lane behaviour can
# be exercised without touching live state or spending a fire.
#
# Lane note: locks live under $ROOT/state/locks, so redirecting ROOT is all the
# isolation the lane slots need -- a test run can never grab a production slot.
set -euo pipefail

SB=${SB:-$(mktemp -d /tmp/amphora-loop-test.XXXXXX)}
SRC=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

sandbox_reset() {
    rm -rf "$SB"; mkdir -p "$SB/state" "$SB/logs" "$SB/lib" "$SB/directives" "$SB/bin"
    # The deployed controller is intentionally mode 0444. The sandbox mutates
    # its own campaign copy, so give that throwaway copy owner-write permission.
    install -m 600 "$SRC/bootstrap/campaign.json" "$SB/campaign.json"
    cp "$SRC/claude-hourly-loop.prompt.txt" "$SB/claude-hourly-loop.prompt.txt"
    cp "$SRC/lib/"*.py "$SB/lib/"
    cp "$SRC/directives/"*.json "$SB/directives/" 2>/dev/null || true

    # fake agent: prints $SB/agent-out, exits $SB/agent-rc, sleeps $SB/agent-sleep
    # seconds first (concurrency tests hold a fire open with it)
    cat > "$SB/bin/claude" <<'FAKE'
#!/usr/bin/env bash
d="$(dirname "$0")/.."
# agent-wedge: hold campaign.lock for N seconds, detached, starting DURING the
# agent phase — i.e. structurally after the claim and before the update. This
# is how tests wedge the update path without racing wall-clock sleeps.
w=$(cat "$d/agent-wedge" 2>/dev/null || echo 0)
if [ "$w" -gt 0 ] 2>/dev/null; then
    ( exec 9>>"$d/state/locks/campaign.lock"; flock 9; sleep "$w" ) >/dev/null 2>&1 &
    sleep 0.3   # let the wedge take the lock before we exit
fi
s=$(cat "$d/agent-sleep" 2>/dev/null || echo 0)
[ "$s" -gt 0 ] 2>/dev/null && sleep "$s"
cat "$d/agent-out" 2>/dev/null || true
exit "$(cat "$d/agent-rc" 2>/dev/null || echo 0)"
FAKE
    chmod +x "$SB/bin/claude"
    echo 0 > "$SB/agent-rc"; : > "$SB/agent-out"; echo 0 > "$SB/agent-sleep"

    # real script, retargeted: sandbox ROOT, fake agent, dead ssh/scp
    # (No DIRECTIVE_INDEX rewrite: the launcher resolves it per-item from the
    # registry, whose paths are ROOT-relative — the ROOT rewrite is enough.)
    sed -e "s|^CONFIG_FILE=.*|CONFIG_FILE=/dev/null|" \
        -e "s|^CONTROLLER_ROOT=.*|CONTROLLER_ROOT=$SB|" \
        -e "s|^ROOT=.*AMPHORA_STATE_ROOT.*|ROOT=$SB|" \
        -e "s|^CLAUDE_BIN=.*AMPHORA_CLAUDE_BIN.*|CLAUDE_BIN=$SB/bin/claude|" \
        -e "s|^SSH=.*AMPHORA_SSH_COMMAND.*|SSH=false|" \
        "$SRC/claude-hourly-loop.sh" > "$SB/claude-hourly-loop.sh"
    chmod +x "$SB/claude-hourly-loop.sh"
    # No transport may reach the network, including a future direct call that
    # bypasses the launcher's parameterized SSH command.
    for transport in ssh scp; do
        printf '#!/bin/sh\nexit 1\n' > "$SB/bin/$transport"
        chmod +x "$SB/bin/$transport"
    done
    grep -q "^CONTROLLER_ROOT=$SB$" "$SB/claude-hourly-loop.sh" || { echo "HARNESS: controller rewrite failed"; exit 1; }
    grep -q "^ROOT=$SB$" "$SB/claude-hourly-loop.sh" || { echo "HARNESS: state ROOT rewrite failed"; exit 1; }
    grep -q "^SSH=false$" "$SB/claude-hourly-loop.sh" || { echo "HARNESS: SSH rewrite failed"; exit 1; }
}

# fire <rc> <transcript> -- one synchronous launcher run (lands on lane 1)
fire() {
    echo "$1" > "$SB/agent-rc"; printf '%s\n' "$2" > "$SB/agent-out"
    PATH="$SB/bin:$PATH" bash "$SB/claude-hourly-loop.sh" >/dev/null 2>&1 || true
}

# fire_bg <rc> <transcript> <sleep_secs> -- background launcher; caller waits.
# The rc/transcript/sleep files are shared knobs: set them BEFORE the batch of
# backgrounded starts, not between them.
fire_bg() {
    echo "$1" > "$SB/agent-rc"; printf '%s\n' "$2" > "$SB/agent-out"; echo "${3:-2}" > "$SB/agent-sleep"
    PATH="$SB/bin:$PATH" bash "$SB/claude-hourly-loop.sh" >/dev/null 2>&1 &
}

st()  { cat "$SB/state/$1" 2>/dev/null || echo "-"; }
# lane logs: lanelog [lane] -> path; tailog reads lane 1 (single-fire tests land there)
lanelog() { echo "$SB/logs/lane-${1:-1}/claude-hourly-loop.log"; }
alllogs() { cat "$SB"/logs/lane-*/claude-hourly-loop.log 2>/dev/null; }
tailog() { tail -n "${1:-15}" "$(lanelog 1)"; }
lastout() { tail -1 "$SB/logs/fire-summary.jsonl" | jq -r '.outcome + " " + (.fire_class // "-") + " rc=" + ((.agent_rc // "null")|tostring)'; }
leases() { jq -r '(.leases // {}) | to_entries[] | .key + " lane=" + (.value.lane|tostring) + " item=" + (.value.item_id|tostring)' "$SB/state/lane-ledger.json" 2>/dev/null; }
nleases() { jq -r '(.leases // {}) | length' "$SB/state/lane-ledger.json" 2>/dev/null || echo 0; }

pass=0; fail=0
check() { # check <label> <expected> <actual>
    if [ "$2" = "$3" ]; then echo "  PASS  $1"; pass=$((pass+1))
    else echo "  FAIL  $1: expected [$2] got [$3]"; fail=$((fail+1)); fi
}
summary() { echo; echo "== $pass passed, $fail failed =="; [ "$fail" -eq 0 ]; }
