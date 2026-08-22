#!/usr/bin/env bash
# Hourly autonomous Claude loop for amphora coating IP portfolio.
# Fully non-interactive:
#   --permission-mode plan       : Claude starts in plan mode
#   --dangerously-skip-permissions: auto-approves ExitPlanMode + all edits/bash
#   -p / --print                 : headless (no TTY prompts)
# Wall clock cap: 55 minutes so an over-running loop never collides with next hour.
# flock ensures only one instance ever runs; concurrent invocation exits silently.
set -euo pipefail

if [ -n "${AMPHORA_ROOT:-}" ]; then
    ROOT=$(cd -- "$AMPHORA_ROOT" && pwd)
else
    SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
    ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
fi
LOCK=/tmp/amphora-claude-hourly-loop.lock
LOG_DIR="$ROOT/logs"
LOG="$LOG_DIR/claude-hourly-loop.log"
PROMPT_FILE="$ROOT/scripts/claude-hourly-loop.prompt.txt"
CLAUDE_BIN=/home/ubuntu/.local/bin/claude
MAX_SECS=3300  # 55 minutes

mkdir -p "$LOG_DIR"

# Non-blocking flock on FD 200. If another instance holds it, exit 0 silently.
exec 200>"$LOCK"
if ! flock -n 200; then
    echo "[$(date -Iseconds)] SKIP: another loop is running (lock held on $LOCK)" >> "$LOG"
    exit 0
fi

# Belt-and-suspenders: also record our PID inside the lock for debugging.
echo $$ > "$LOCK"

cd "$ROOT"

{
    echo ""
    echo "=================================================================="
    echo "=== $(date -Iseconds) START pid=$$ host=$(hostname) ==="
    echo "=================================================================="
    echo "cwd: $(pwd)"
    echo "claude: $CLAUDE_BIN ($($CLAUDE_BIN --version 2>&1 | head -1))"
    echo ""

    # Read prompt from file so it can be edited without touching this script.
    if [ ! -f "$PROMPT_FILE" ]; then
        echo "FATAL: prompt file missing at $PROMPT_FILE"
        exit 2
    fi

    # Plan-mode + auto-approve + headless. Prompt piped on stdin.
    # `timeout --foreground` sends SIGTERM at MAX_SECS; SIGKILL 30s later if needed.
    set +e
    timeout --foreground --kill-after=30s "${MAX_SECS}s" \
        "$CLAUDE_BIN" \
            --permission-mode plan \
            --dangerously-skip-permissions \
            -p \
        < "$PROMPT_FILE"
    rc=$?
    set -e

    echo ""
    echo "=================================================================="
    echo "=== $(date -Iseconds) END exit=$rc ==="
    echo "=================================================================="
} >> "$LOG" 2>&1
