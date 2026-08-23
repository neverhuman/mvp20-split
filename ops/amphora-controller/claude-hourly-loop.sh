#!/usr/bin/env bash
# Autonomous Claude loop for the Amphora coating IP portfolio — v5 (lanes).
#
# v5 (2026-08-10) — FOUR CONCURRENT LANES, capped structurally.
# One cron entry (*/15) starts one launcher; each launcher must win one of
# exactly LANE_COUNT slot locks or exit, so no crontab mistake can ever run a
# fifth. Lanes coordinate through a module-lease ledger: a lane owns its target
# module for the duration of its fire (TTL-bounded, so a killed lane self-heals),
# which is the invariant that keeps the pre/post content-hash attribution sound.
# Everything shared — campaign.json, the lease ledger, every state counter and
# gate — mutates only inside one of two flocks, in a fixed total order:
#     slot(1) -> fleet(2) -> campaign.lock(3) -> state.lock(4)
# ascending only, 3 and 4 never held together, no ssh/scp held under 3 or 4
# (sole bounded exception: announce_stall's mirror_line, ConnectTimeout 15s).
# Counters are re-read INSIDE the lock before every increment: a value read
# pre-fire is 10-55 minutes stale by post-fire and writing from it can walk a
# counter backwards. "Consecutive" now means fleet completion order.
# campaign.json left the tamper-evidence baseline (the loop is DESIGNED to
# write it; a sibling's legitimate update tripped a fleet HARD_STOP otherwise)
# and is instead hash-chained through the lease history: every mutation records
# pre/post sha256 and the claim step verifies the chain.
#
# v3 (2026-08-02) — hardened against a CONCURRENT-WRITER threat model.
# v2 assumed the cron was the only writer on xbabe2. It is not: interactive
# claude/codex sessions run there as the same uid. Every v2 verification signal
# was a time-windowed observation of shared mutable state; v3 replaces all of
# them with identity-bound, content-hashed, cryptographically-verified evidence.
#
#   A1 injection    ssh no longer re-parses any value. All remote params travel
#                   as ONE base64-JSON argv token. TARGET is regex-validated.
#                   (v2's `ssh bash -s "$TARGET"` was a proven RCE.)
#   A2 attribution  find -newermt REPLACED by a pre/post CONTENT-HASH set-diff
#                   scoped to the target module, intersected with the agent's
#                   DECLARED artifacts. Kills touch/symlink/wrong-module/
#                   timestamp-race/bystander-credit at once.
#   A3 ledger       must contain a line bearing THIS fire's FIRE_ID; growth by
#                   line count is no longer trusted.
#   A4 fail-closed  a missing snapshot/ledger baseline BLOCKS verdict acceptance
#                   instead of silently passing (v2 had two fail-opens).
#   A5 done_check   structured object only; a string or absent check BLOCKS the
#                   done transition (v2 treated "none-defined" as pass).
#   A6 DSSE         real Ed25519 over the DSSE PAE encoding against the pinned
#                   Phase-0 key (v2 accepted any `{"signature":{}}`).
#   A7 guard tiers  IMMUTABLE=hard-stop, COLLABORATIVE=log-only. settings.json
#                   dropped (the CLI rewrites it on /model — near-miss stop).
#   A8 state        max ts, not `tail -1` (unsound on a multi-writer file).
#   A9 reserved     operator_reserved_paths fence. (The "cross-host flock" this
#                   line once claimed was never implemented; v5 replaced the
#                   idea with module leases, which actually exist.)
#   A10 robustness  set -E, ERR trap before first mkdir, EXIT cleanup, summary
#                   built via stdin (argv hit E2BIG), duplicate-id rejection,
#                   cron-audit pruning.
set -Eeuo pipefail

# Configuration is intentionally a small KEY=VALUE file rather than sourced
# shell.  Environment variables win over file values, and unknown keys are
# ignored.  This keeps cron configuration auditable and prevents a typo in the
# file from executing shell code.
CONFIG_FILE=${AMPHORA_CONFIG_FILE:-/home/ubuntu/.config/amphora/mvp20-cron.env}
if [ -r "$CONFIG_FILE" ]; then
    while IFS='=' read -r config_key config_value; do
        config_key=${config_key%%[[:space:]]*}
        case "$config_key" in
            AMPHORA_CONTROLLER_ROOT|AMPHORA_STATE_ROOT|AMPHORA_CAMPAIGN_PATH|AMPHORA_QUEUE_PATH|AMPHORA_PROMPT_PATH|AMPHORA_DIRECTIVE_REGISTRY|AMPHORA_TARGET_HOST|AMPHORA_TARGET_ROOT|AMPHORA_MODEL|AMPHORA_CLAUDE_BIN|AMPHORA_SIGNING_KEY_PATH|AMPHORA_SSH_COMMAND)
                if [ -n "$config_key" ] && [ -z "${!config_key+x}" ]; then
                    config_value=${config_value%$'\r'}
                    config_value=${config_value#\"}; config_value=${config_value%\"}
                    config_value=${config_value#\'}; config_value=${config_value%\'}
                    printf -v "$config_key" '%s' "$config_value"
                fi
                ;;
        esac
    done < "$CONFIG_FILE"
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CONTROLLER_ROOT=${AMPHORA_CONTROLLER_ROOT:-$SCRIPT_DIR}
ROOT=${AMPHORA_STATE_ROOT:-/home/ubuntu/amphora-cron}
LOG_DIR="$ROOT/logs"
FIRE_SUMMARY="$LOG_DIR/fire-summary.jsonl"
CAMPAIGN=${AMPHORA_CAMPAIGN_PATH:-$ROOT/campaign.json}
STATE_DIR="$ROOT/state"
# Locks live under the tree, not /tmp: the sandbox harness redirects ROOT, so
# test runs can never grab a production lane slot.
LOCK_DIR="$STATE_DIR/locks"
LANE_COUNT=4               # the hard cap; slots are the enforcement, not cron
LANE=""                    # assigned by slot acquisition
SLOT_FD=""                 # Bash dynamic fd copied from slotfd after acquisition
LOG="$LOG_DIR/launcher.log"   # bootstrap log until a slot names the lane
LANE_LEDGER="$STATE_DIR/lane-ledger.json"
LANE_HISTORY="$STATE_DIR/lane-ledger.history.jsonl"
CAMPAIGN_LOCK="$LOCK_DIR/campaign.lock"
STATE_LOCK="$LOCK_DIR/state.lock"
FLEET_LOCK="$LOCK_DIR/fleet.lock"
NO_PROGRESS_FILE="$STATE_DIR/consecutive-no-progress.txt"
INFRA_FAIL_FILE="$STATE_DIR/consecutive-infra-fail.txt"
QUOTA_HOLD_FILE="$STATE_DIR/quota-hold-until"
GATE_HOLD_FILE="$STATE_DIR/gate-hold-until"
GATE_LEVEL_FILE="$STATE_DIR/gate-hold-level"
STALLED_FILE="$STATE_DIR/STALLED"
HARD_STOP_FILE="$STATE_DIR/HARD_STOP"
AUTOCOMMIT_DRAIN_FILE="$STATE_DIR/AUTOCOMMIT_DRAIN"
MIRROR_SHA_FILE="$STATE_DIR/last-mirrored.sha256"
DATA_ASK_QUEUE=${AMPHORA_QUEUE_PATH:-$ROOT/data-acquisition-queue.jsonl}
PROMPT_TEMPLATE=${AMPHORA_PROMPT_PATH:-$CONTROLLER_ROOT/claude-hourly-loop.prompt.txt}
REMOTE_VERIFY="$CONTROLLER_ROOT/lib/remote_verify.py"
CLAUDE_BIN=${AMPHORA_CLAUDE_BIN:-/home/ubuntu/.local/bin/claude}
MODEL=${AMPHORA_MODEL:-claude-sonnet-5}
XBABE2_HOST=${AMPHORA_TARGET_HOST:-xbabe2}
XBABE2_ROOT=${AMPHORA_TARGET_ROOT:-/home/ubuntu/amphora/build/mvp20-split}
SIGNING_KEY_PATH=${AMPHORA_SIGNING_KEY_PATH:-/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed}
XBABE2_LOG="$XBABE2_ROOT/logs/claude-hourly-loop.log"
LEDGER="$XBABE2_ROOT/logs/falsification-ledger.jsonl"
# Founder directive spine, plural (v5). REGISTRY.json routes a campaign item's
# directive_ref.doc to its index; the index alone carries the document's path
# and sha256. Both the registry and every registered index are IMMUTABLE-tier,
# so tampering with what we owe the founder hard-stops. An item citing a doc
# the registry does not know FAILS CLOSED: its verdicts are never accepted.
DIRECTIVE_REGISTRY=${AMPHORA_DIRECTIVE_REGISTRY:-$CONTROLLER_ROOT/directives/REGISTRY.json}
DIRECTIVE_INDEX=""   # resolved per-item from the registry; empty = item has no directive_ref
AUDIT_DIR="$XBABE2_ROOT/logs/cron-audit"
# (v5 removed XBABE2_LOCK: it was assigned and never flocked -- the header's
# old "A9 cross-host flock" claim was unimplemented, the CORRECTIONS.md defect
# class. Cross-lane exclusion on xbabe2 is the module lease, which is real.)
MASTER_MANIFEST="$XBABE2_ROOT/amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json"
MAX_SECS=3300
SATURATION_THRESHOLD=3
AUDIT_KEEP=160             # 4 lanes push ~12 files/hr; 40 held only ~3h of history
# A lease must outlive the WORST run, not the typical one: agent (MAX_SECS) +
# kill grace + a post-fire phase of ~8 serial ssh round-trips that has no
# deadline of its own. A reaped-live lease puts two agents in one module, which
# silently breaks content-hash attribution -- the one unforgivable failure.
LEASE_TTL=$(( MAX_SECS + 30 + 1800 ))
export DISABLE_AUTOUPDATER=1   # 4 CLIs racing to self-replace the binary corrupt it
# v4: a stall must expire on its own. The saturation gate was a latch; on
# 2026-08-06 three usage-limit refusals tripped it and it held for 80 hours
# because only a human typing `echo 0 >` could release it. Holds are now timed
# and self-releasing, and infrastructure failure is counted apart from
# epistemic exhaustion so the two can never be confused again.
INFRA_THRESHOLD=6          # consecutive never-ran fires before the infra gate holds
GATE_HOLD_BASE=3600        # first hold; doubles on each fruitless probe
GATE_HOLD_MAX=86400        # 24h ceiling on a single hold
GATE_LEVEL_MAX=20          # keeps the doubling shift far from integer overflow
QUOTA_FALLBACK_SECS=21600  # 6h hold when the reset time cannot be parsed
QUOTA_HOLD_MAX=691200      # 8d ceiling: a bad parse must not wedge the loop
STALL_RENOTIFY_SECS=21600  # re-announce a held gate every 6h

# ServerAlive bounds an established-but-stalled channel (~45s worst case);
# ConnectTimeout alone only bounds establishment. This also caps how long an
# orphaned ssh child can outlive a killed launcher while holding inherited fds.
SSH=${AMPHORA_SSH_COMMAND:-"ssh -o ConnectTimeout=15 -o BatchMode=yes -o ServerAliveInterval=5 -o ServerAliveCountMax=6"}

main() {

# --- A10: trap installed BEFORE any filesystem work, so a full disk is loud --
# mirror_line runs in a subshell that CLOSES every lock fd and carries a hard
# deadline. Review finding (2026-08-10): ConnectTimeout bounds only connection
# establishment — an established-but-stalled channel hung forever, and because
# children inherit flocked fds, an operator kill -9 of the launcher left the
# orphan ssh holding the state lock AND the lane slot: the whole fleet stopped,
# silently, with nothing to say so. The fd closes make an orphan lock-free; the
# timeout bounds the in-lock hold even before any kill.
mirror_line() {
    (
        exec 220>&- 221>&- 2>/dev/null || true
        [ -n "${SLOT_FD:-}" ]  && eval "exec $SLOT_FD>&-"  || true
        [ -n "${FLEET_FD:-}" ] && eval "exec $FLEET_FD>&-" || true
        # SSH is the reviewed command plus options, matching every call below.
        # shellcheck disable=SC2086
        exec timeout 25s $SSH "$XBABE2_HOST" "cat >> '$XBABE2_LOG'"
    ) <<< "$1" >/dev/null 2>&1 || true
}
on_err() {
    local ec=$? ln=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}
    local msg
    msg="[$(date -Iseconds)] FATAL: line $ln: $cmd (rc=$ec) — post-processing aborted"
    echo "$msg" >> "$LOG" 2>/dev/null || true
    mirror_line "$msg"
}
trap on_err ERR
trap 'rm -f "${FIRE_PROMPT:-}" "${PROT_PRE:-}" "${PROT_POST:-}" "${SNAP_PRE:-}" "${VERIFY_OUT:-}" 2>/dev/null || true' EXIT

# --- counter/state readers ---------------------------------------------------
# Every gate reads a small integer from a file another process may be mid-write
# on. A partial or hand-edited value must degrade to 0 (fire) rather than to a
# shell error under `set -u`/`set -e`.
read_num() {
    local v; v=$(head -1 "$1" 2>/dev/null || echo 0)
    [[ "$v" =~ ^[0-9]+$ ]] && echo "$v" || echo 0
}

hb_event() {   # $1=event name, $2=optional pre-encoded JSON k:v tail
    printf '{"ts":"%s","event":"%s","host":"xbabe1","pid":%s,"lane":"%s"%s}\n' \
        "$(date -Iseconds)" "$1" "$$" "${LANE:-0}" "${2:+,$2}" \
        >> "$LOG_DIR/heartbeat.jsonl" 2>/dev/null || true
}

skip_record() {  # $1=outcome $2=notes -- one fire-summary row for a fire not run
    jq -n --arg ts "$(date -Iseconds)" --arg model "$MODEL" --arg o "$1" --arg n "$2" \
       --arg lane "${LANE:-0}" \
       '{ts:$ts,module:null,mode:null,model:$model,outcome:$o,runtime_s:0,
         artifacts:[],receipts_added:0,data_asks_added:0,notes:$n,
         agent_rc:null,fire_class:"NOT_RUN",lane:$lane}' \
       | jq -c . >> "$FIRE_SUMMARY" || true
}

# --- fleet state lock --------------------------------------------------------
# fd 220 stays open for the whole run; critical sections flock/funlock it.
# Locked sections are milliseconds of local file work -- never remote calls --
# so -w 30 failing means something is wedged, and the safe answer is to skip
# this slot (no counter movement: a declined start is not evidence of anything).
state_lock()   { flock -w 30 220; }
state_unlock() { flock -u 220 || true; }

# --- stall surfacing ---------------------------------------------------------
# The 80-hour stall of 2026-08-06 was invisible: the only trace was a log line
# identical to the 79 before it. A held gate now writes a state file, emits a
# heartbeat event, and pushes a distinct ALERT down the xbabe2 mirror -- the
# same path LEDGER_REWRITTEN and PROTECTED_FILE_MODIFIED already use. It
# re-announces every STALL_RENOTIFY_SECS so a long hold keeps saying so.
announce_stall() {  # $1=kind $2=reason $3=release epoch (0 = manual only)
    local kind=$1 reason=$2 release=$3 now last=0 since rel
    now=$(date +%s); since=$now
    if [ -f "$STALLED_FILE" ]; then
        local prev_kind; prev_kind=$(jq -r '.kind // ""' "$STALLED_FILE" 2>/dev/null || echo "")
        if [ "$prev_kind" = "$kind" ]; then
            last=$(read_num_json "$STALLED_FILE" last_announced_epoch)
            since=$(read_num_json "$STALLED_FILE" held_since_epoch)
            [ "$since" -eq 0 ] && since=$now
        fi
    fi
    rel=manual; [ "$release" -gt 0 ] && rel=$(date -Iseconds -d "@$release")
    if [ "$last" -eq 0 ] || [ $(( now - last )) -ge "$STALL_RENOTIFY_SECS" ]; then
        local msg
        msg="[$(date -Iseconds)] ALERT STALLED[$kind]: $reason — held since $(date -Iseconds -d "@$since"), auto-release $rel"
        echo "$msg" >> "$LOG"; mirror_line "$msg"
        hb_event stalled "$(jq -cn --arg k "$kind" --arg r "$reason" --arg s "$(date -Iseconds -d "@$since")" --arg a "$rel" \
            '{kind:$k,reason:$r,held_since:$s,release_at:$a}' | sed 's/^{//;s/}$//')"
        last=$now
    fi
    jq -n --arg k "$kind" --arg r "$reason" --argjson s "$since" --argjson l "$last" \
          --argjson rel "$release" --arg relh "$rel" \
       '{kind:$k,reason:$r,held_since_epoch:$s,held_since:($s|todate),
         last_announced_epoch:$l,release_epoch:$rel,release:$relh}' \
       > "$STALLED_FILE" 2>/dev/null || true
}
read_num_json() {  # $1=file $2=key -- integer or 0
    local v; v=$(jq -r --arg k "$2" '.[$k] // 0' "$1" 2>/dev/null || echo 0)
    [[ "$v" =~ ^[0-9]+$ ]] && echo "$v" || echo 0
}
clear_stall() {
    if [ -f "$STALLED_FILE" ]; then
        rm -f "$STALLED_FILE"
        echo "[$(date -Iseconds)] RECOVERED: stall cleared, loop firing normally" >> "$LOG"
        hb_event recovered ""
    fi
}

mkdir -p "$LOG_DIR" "$STATE_DIR" "$LOCK_DIR"
touch "$FIRE_SUMMARY" "$DATA_ASK_QUEUE"
[ -f "$NO_PROGRESS_FILE" ] || echo 0 > "$NO_PROGRESS_FILE"
[ -f "$INFRA_FAIL_FILE" ]  || echo 0 > "$INFRA_FAIL_FILE"

# --- lane slot acquisition (lock order position 1) ---------------------------
# Win exactly one of LANE_COUNT slots or exit. The cap is structural: however
# many cron entries or manual starts exist, a fifth concurrent launcher has no
# slot to win. flock releases on process death, so a killed lane frees its slot
# instantly; the module lease (TTL) is what protects mid-fire state, not this.
for i in $(seq 1 "$LANE_COUNT"); do
    # Open in APPEND mode: opening with > would O_TRUNC the pid breadcrumb the
    # current holder wrote, on every probe of a busy slot (review finding).
    exec {slotfd}>>"$LOCK_DIR/lane-$i.lock"
    if flock -n "$slotfd"; then
        LANE=$i; SLOT_FD=$slotfd
        echo $$ > "$LOCK_DIR/lane-$i.lock"
        break
    fi
    exec {slotfd}>&-
done
if [ -z "$LANE" ]; then
    hb_event lanes_full ""
    exit 0
fi

# Position 2: shared fleet lock, held for the whole run. An exclusive probe
# (`flock -n -x`) answers "is any lane running?" for ops and the deploy drain.
# Non-blocking: while ops holds the exclusive lock (a drain), new starts EXIT
# instead of queueing up behind it — and a failure never proceeds unlocked,
# or the drain probe would read "idle" over a running lane.
exec {FLEET_FD}>"$FLEET_LOCK"
if ! flock -s -n "$FLEET_FD"; then
    hb_event fleet_drained ""
    exit 0
fi

# Position 4's fd, opened now, locked only inside critical sections.
exec 220>"$STATE_LOCK"

# The lane owns its own log: byte-offset transcript slicing is only sound with
# a single writer, and under v4's shared log one lane's quota refusal classified
# every lane as QUOTA while a summary-less lane silently adopted a sibling's.
LOG="$LOG_DIR/lane-$LANE/claude-hourly-loop.log"
mkdir -p "$LOG_DIR/lane-$LANE"
touch "$LOG"

# --- G2 heartbeat: an hour where the agent never starts must still leave a
# --- trace. 3 hours are missing from the record with no evidence at all. ---
hb_event fire_attempt ""

if [ -f "$HARD_STOP_FILE" ]; then
    S="[$(date -Iseconds)] HARD_STOP_SKIP: $(head -1 "$HARD_STOP_FILE"). Unblock: review + delete $HARD_STOP_FILE, then reset $NO_PROGRESS_FILE."
    echo "$S" >> "$LOG"; mirror_line "$S"; exit 0
fi
if [ -f "$AUTOCOMMIT_DRAIN_FILE" ]; then
    S="[$(date -Iseconds)] AUTOCOMMIT_DRAIN_SKIP: $(head -1 "$AUTOCOMMIT_DRAIN_FILE"). The guarded snapshot owns the fleet drain."
    echo "$S" >> "$LOG"; mirror_line "$S"; exit 0
fi

# --- A8: max ts across the file, never `tail -1` (multi-writer unsound) ------
# Rows for fires that were SKIPPED are excluded. The gate appends one row per
# hour it blocks, so counting them made this warning measure "time since the
# loop last did anything at all, including nothing" -- it could not fire during
# the very stall it exists to catch, and did not during the 80-hour one.
LAST_TS=$(jq -rs 'map(select(((.outcome // "") | test("_SKIP$|^QUOTA_HOLD$")) | not) | .ts // empty)|max // empty' \
    "$FIRE_SUMMARY" 2>/dev/null || true)
if [ -n "${LAST_TS:-}" ]; then
    GAP=$(( $(date +%s) - $(date -d "$LAST_TS" +%s 2>/dev/null || date +%s) ))
    if [ "$GAP" -gt 7200 ]; then
        S="[$(date -Iseconds)] WARN MISSED_HOURS: ${GAP}s since the last fire that actually ran ($LAST_TS)"
        echo "$S" >> "$LOG"; mirror_line "$S"
    fi
fi

NOW_EPOCH=$(date +%s)

# --- PREFLIGHT: one critical section (lock order position 4) -----------------
# Quota expiry, gate trip, probe spending and hold clearing are read-decide-
# write over shared state. Under 4 lanes they must be atomic as a WHOLE: two
# lanes that both read an expired hold before either re-arms it would both
# spend "the one probe". Exits inside the section release the flock at process
# death, which is the correct semantic for a skip.
if ! state_lock; then
    hb_event state_lock_timeout '"where":"preflight"'
    echo "[$(date -Iseconds)] STATE_LOCK_TIMEOUT: preflight — skipping this slot, no counters moved" >> "$LOG"
    exit 0
fi

# --- quota hold --------------------------------------------------------------
# A usage limit is not an exhausted portfolio; it is the agent never running.
# Hold cheaply until the stated reset instead of spending fires that cannot work
# and cannot learn -- which is exactly how the 2026-08-06 stall began.
QUOTA_UNTIL=$(read_num "$QUOTA_HOLD_FILE")
if [ "$QUOTA_UNTIL" -gt "$NOW_EPOCH" ]; then
    announce_stall QUOTA "usage limit reached; no fire can do work until it resets" "$QUOTA_UNTIL"
    S="[$(date -Iseconds)] QUOTA_HOLD: skipping until $(date -Iseconds -d "@$QUOTA_UNTIL") — not counted against saturation"
    echo "$S" >> "$LOG"
    skip_record QUOTA_HOLD "quota hold until $(date -Iseconds -d "@$QUOTA_UNTIL")"
    exit 0
elif [ "$QUOTA_UNTIL" -gt 0 ]; then
    rm -f "$QUOTA_HOLD_FILE"
    echo "[$(date -Iseconds)] QUOTA_HOLD_EXPIRED: limit window passed, resuming" >> "$LOG"
    clear_stall
fi

# --- backoff gate: epistemic saturation OR sustained infrastructure failure ---
# One hold mechanism serves both, so a stall has exactly one place to live and
# exactly one way out. On trip the loop holds an hour; when the hold expires it
# spends ONE probe fire, and if that probe banks nothing the hold doubles
# (1h,2h,4h,8h,16h,24h cap). A verified verdict clears the hold at any level.
NO_PROGRESS=$(read_num "$NO_PROGRESS_FILE")
INFRA_FAILS=$(read_num "$INFRA_FAIL_FILE")
GATE_UNTIL=$(read_num "$GATE_HOLD_FILE")
GATE_LEVEL=$(read_num "$GATE_LEVEL_FILE")
GATE_KIND=""
[ "$NO_PROGRESS" -ge "$SATURATION_THRESHOLD" ] && GATE_KIND=SATURATION
[ "$INFRA_FAILS"  -ge "$INFRA_THRESHOLD"     ] && GATE_KIND=INFRA

if [ -n "$GATE_KIND" ]; then
    if [ "$GATE_UNTIL" -eq 0 ]; then          # just tripped: open the hold
        GATE_LEVEL=1
        GATE_UNTIL=$(( NOW_EPOCH + GATE_HOLD_BASE ))
        echo "$GATE_LEVEL" > "$GATE_LEVEL_FILE"
        echo "$GATE_UNTIL" > "$GATE_HOLD_FILE"
    fi
    if [ "$NOW_EPOCH" -lt "$GATE_UNTIL" ]; then
        case "$GATE_KIND" in
          SATURATION) GATE_REASON="$NO_PROGRESS consecutive fires that ran but banked no verified information" ;;
          *)          GATE_REASON="$INFRA_FAILS consecutive fires that never produced a result (quota, network, or timeout)" ;;
        esac
        announce_stall "$GATE_KIND" "$GATE_REASON" "$GATE_UNTIL"
        S="[$(date -Iseconds)] ${GATE_KIND}_SKIP: $GATE_REASON. Auto-probe at $(date -Iseconds -d "@$GATE_UNTIL") (hold level $GATE_LEVEL). Force now: echo 0 > $NO_PROGRESS_FILE && echo 0 > $INFRA_FAIL_FILE"
        echo "$S" >> "$LOG"; mirror_line "$S"
        skip_record "${GATE_KIND}_SKIP" "backoff hold level $GATE_LEVEL until $(date -Iseconds -d "@$GATE_UNTIL")"
        exit 0
    fi
    # Hold expired: spend ONE probe. Arm the next (longer) hold up front and set
    # the counter one short of its threshold, so a single fruitless probe
    # re-holds immediately while a successful one clears everything below.
    if [ "$GATE_LEVEL" -lt "$GATE_LEVEL_MAX" ]; then GATE_LEVEL=$(( GATE_LEVEL + 1 )); fi
    echo "$GATE_LEVEL" > "$GATE_LEVEL_FILE"
    NEXT_HOLD=$(( GATE_HOLD_BASE * (1 << (GATE_LEVEL - 1)) ))
    if [ "$NEXT_HOLD" -gt "$GATE_HOLD_MAX" ]; then NEXT_HOLD=$GATE_HOLD_MAX; fi
    echo $(( NOW_EPOCH + NEXT_HOLD )) > "$GATE_HOLD_FILE"
    case "$GATE_KIND" in
      SATURATION) NO_PROGRESS=$(( SATURATION_THRESHOLD - 1 )); echo "$NO_PROGRESS" > "$NO_PROGRESS_FILE" ;;
      *)          INFRA_FAILS=$(( INFRA_THRESHOLD - 1 ));      echo "$INFRA_FAILS"  > "$INFRA_FAIL_FILE"  ;;
    esac
    echo "[$(date -Iseconds)] GATE_PROBE: $GATE_KIND hold expired — spending one probe fire; if it banks nothing the gate re-holds ${NEXT_HOLD}s (level $GATE_LEVEL)" >> "$LOG"
elif [ "$GATE_UNTIL" -gt "$NOW_EPOCH" ] && { [ "$NO_PROGRESS" -gt 0 ] || [ "$INFRA_FAILS" -gt 0 ]; }; then
    # A hold is armed while the counters sit BELOW threshold but above zero:
    # that is the probe-in-flight state (the probe re-arms the hold and sets
    # its counter to threshold-1 before firing). A sibling lane arriving here
    # must not read "sub-threshold" as "cleared" -- v5's first draft did, and
    # the sibling both spent a second probe and deleted the fresh hold. The
    # probe's own outcome decides; everyone else waits.
    S="[$(date -Iseconds)] PROBE_WAIT: a sibling lane's probe is in flight (hold until $(date -Iseconds -d "@$GATE_UNTIL"), level $GATE_LEVEL) — declining this slot"
    echo "$S" >> "$LOG"
    skip_record PROBE_WAIT_SKIP "sibling probe in flight, hold level $GATE_LEVEL"
    exit 0
elif { [ "$GATE_UNTIL" -ne 0 ] || [ "$GATE_LEVEL" -ne 0 ]; } \
     && [ "$NO_PROGRESS" -eq 0 ] && [ "$INFRA_FAILS" -eq 0 ]; then
    # Hold artifacts exist with both counters at zero: a manual `echo 0 >`
    # unblock or a cleared gate. No hold may survive to be inherited.
    # BOTH-zero is load-bearing (review finding): an INFRA-classed probe
    # leaves the counters split sub-threshold, and deleting the hold there
    # logged RECOVERED while nothing had recovered. With counters nonzero the
    # hold artifacts stay; the next fruitless fire re-trips the gate and the
    # backoff ladder continues where it left off.
    rm -f "$GATE_HOLD_FILE" "$GATE_LEVEL_FILE"
    clear_stall
fi
state_unlock

# The lease needs the fire's identity, so the id is minted before the claim.
FIRE_ID="$(date +%Y%m%dT%H%M%S)-$$-$(head -c6 /dev/urandom | od -An -tx1 | tr -d ' \n')"

# --- CLAIM: pick + module lease, atomically (lock order position 3) ----------
# The v3 picker returned the first pending item and RESERVED NOTHING -- four
# concurrent picks returned four copies of the same item. The claim now happens
# inside campaign.lock and writes a module lease before releasing it, so no two
# lanes can ever work the same item or the same module. Expired leases (a lane
# SIGKILLed mid-fire) are reaped here, and every campaign mutation extends a
# pre/post sha256 hash chain in the lease history -- the tamper coverage that
# moving campaign.json out of the immutable baseline would otherwise have lost.
exec 221>"$CAMPAIGN_LOCK"
if ! flock -w 30 221; then
    hb_event claim_lock_timeout ""
    echo "[$(date -Iseconds)] CLAIM_LOCK_TIMEOUT: skipping this slot, no counters moved" >> "$LOG"
    # _SKIP suffix keeps the row out of MISSED_HOURS' last-real-fire scan --
    # a wedged campaign.lock must not suppress the stall warning built for it.
    skip_record CLAIM_LOCK_TIMEOUT_SKIP "campaign.lock not acquired in 30s"
    exit 0
fi
PICK=$(LANE="$LANE" FIRE_ID="$FIRE_ID" LEASE_TTL="$LEASE_TTL" \
       python3 - "$CAMPAIGN" "$LANE_LEDGER" "$LANE_HISTORY" <<'PYEOF' || true
import hashlib, json, os, sys, tempfile, datetime

camp_path, ledger_path, hist_path = sys.argv[1], sys.argv[2], sys.argv[3]
lane, fire_id = os.environ["LANE"], os.environ["FIRE_ID"]
ttl = int(os.environ["LEASE_TTL"])
now_dt = datetime.datetime.now(datetime.timezone.utc)
now = now_dt.isoformat(timespec="seconds")
now_epoch = int(now_dt.timestamp())

raw = open(camp_path, "rb").read()
pre_sha = hashlib.sha256(raw).hexdigest()
c = json.loads(raw)

def hist(event, **kw):
    rec = {"ts": now, "event": event, "lane": lane, "fire_id": fire_id}
    rec.update(kw)
    with open(hist_path, "a") as fh:
        fh.write(json.dumps(rec) + "\n")

# Campaign hash chain: the last recorded post_sha256 must match the bytes just
# read, or the queue was edited outside campaign.lock (an operator, perhaps
# legitimately; an agent, not). Alert-tier, never a stop -- record the rebase
# so the out-of-band edit is a visible event, then continue on the live bytes.
chain_alert = ""
last_post = ""
try:
    with open(hist_path) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("campaign_post_sha256"):
                last_post = r["campaign_post_sha256"]
except FileNotFoundError:
    pass
if last_post and last_post != pre_sha:
    chain_alert = "campaign.json sha %s… does not match last recorded %s… — edited outside campaign.lock" % (pre_sha[:12], last_post[:12])
    hist("chain_rebase", campaign_pre_sha256=pre_sha, expected_post_sha256=last_post)

# Module leases: reap the expired (a killed lane self-heals here), then treat
# every live-leased module as invisible to this pick.
try:
    with open(ledger_path) as fh:
        ledger = json.load(fh)
except (FileNotFoundError, ValueError):
    ledger = {"leases": {}}
leases = ledger.setdefault("leases", {})
for mod in list(leases):
    if int(leases[mod].get("expires", 0)) <= now_epoch:
        hist("expire", module=mod, expired_lease=leases.pop(mod))

def save_ledger():
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ledger_path), prefix=".lane-ledger.")
    with os.fdopen(fd, "w") as fh:
        json.dump(ledger, fh, indent=2); fh.write("\n")
    os.replace(tmp, ledger_path)

post_sha = pre_sha
def atomic(obj):
    global post_sha
    body = json.dumps(obj, indent=2) + "\n"
    post_sha = hashlib.sha256(body.encode()).hexdigest()
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(camp_path), prefix=".campaign.")
    with os.fdopen(fd, "w") as fh:
        fh.write(body)
    os.replace(tmp, camp_path)

ids = [i.get("id") for i in c["items"]]
dupes = {i for i in ids if ids.count(i) > 1}
if dupes:                                   # A10: duplicate ids corrupt accounting
    print(json.dumps({"mode":"ERROR","error":"duplicate campaign ids: %s" % sorted(dupes)})); sys.exit(0)

changed, pick, owner_skipped, leased_skipped, auto_blocked = False, None, [], [], []
for item in c["items"]:
    if item.get("status") != "pending": continue
    # OWNER GUARD. Obligations the founder or a lab must own (directive_ref.owner
    # HUMAN or LAB) must never be dispatched to a fire. Until now the only thing
    # stopping that was that they all happened to be status=blocked -- a data
    # state, not an invariant. Commit 8d76070 claimed a validator enforced this;
    # it did not (see directives/CORRECTIONS.md). This is the enforcement.
    owner = (item.get("directive_ref") or {}).get("owner")
    if owner in ("HUMAN", "LAB"):
        owner_skipped.append("%s(%s)" % (item.get("id"), owner))
        continue
    # max_fires budgets ATTEMPTS BY AN AGENT THAT RAN. A quota refusal, timeout
    # or CLI crash never ran -- burning budget on those silently auto-blocked
    # items during outages (review finding: the whole PROBE-WEB program was one
    # quota refusal from permanent silent loss). Legacy fire records without a
    # fire_class count as run.
    ran = [f for f in item.get("fires", []) if f.get("fire_class", "OK") == "OK"]
    if len(ran) >= int(item.get("max_fires", 6)):
        item["status"]="blocked"; item["blocked_reason"]="auto_blocked_max_fires at %s"%now
        auto_blocked.append(item.get("id"))
        changed=True; continue
    if item.get("module") in leases:        # a sibling lane owns this module
        leased_skipped.append("%s(%s)" % (item.get("id"), item.get("module")))
        continue
    pick=item; break
if changed:
    atomic(c)
    # An auto-block is a campaign mutation and a decision: it gets its own
    # chain-bearing history event even when no pick follows -- the first draft
    # recorded no post_sha on the no-claimable path after an auto-block, and
    # the next claim's chain check read its own write as tamper.
    hist("auto_block", items=auto_blocked,
         campaign_pre_sha256=pre_sha, campaign_post_sha256=post_sha)

pending = sum(1 for i in c["items"] if i.get("status")=="pending")
reserved = c.get("operator_reserved_paths") or []
# Module backlog health: a module with no pending item makes no progress, and one
# with a single item is one fire from that. Surfaced per fire so it is noticed
# mechanically rather than by someone remembering to look.
_mods = {i.get("module") for i in c["items"] if i.get("module")}
_pend = {}
for i in c["items"]:
    if i.get("status") == "pending" and i.get("module"):
        _pend[i["module"]] = _pend.get(i["module"], 0) + 1
empty_mods = sorted(_mods - set(_pend))
low_mods = sorted(m for m, n in _pend.items() if n == 1)

common = {"pending": pending, "reserved": reserved, "owner_skipped": owner_skipped,
          "leased_skipped": leased_skipped, "empty_modules": empty_mods,
          "low_modules": low_mods, "chain_alert": chain_alert}

def take_lease(module, item_id):
    leases[module] = {"lane": lane, "fire_id": fire_id, "item_id": item_id,
                      "ts": now, "expires": now_epoch + ttl}
    save_ledger()
    hist("claim", module=module, item_id=item_id,
         campaign_pre_sha256=pre_sha, campaign_post_sha256=post_sha)

if pick is not None:
    take_lease(pick["module"], pick["id"])
    print(json.dumps(dict(common, mode="CAMPAIGN", module=pick["module"],
                          item_id=pick["id"], item=pick))); sys.exit(0)

if pending > 0:
    # Work exists but every claimable module is a sibling's. Declining the slot
    # costs one 15-minute tick; stepping into a leased module costs attribution.
    hist("no_claimable", pending=pending)
    print(json.dumps(dict(common, mode="NO_CLAIMABLE", module=None, item_id=None, item=None))); sys.exit(0)

rot=c["fallback_rotation"]; mods=rot["modules"]
sched=sorted(((k+1)/max(1,int(m.get("weight",1))), i) for i,m in enumerate(mods)
             for k in range(max(1,int(m.get("weight",1)))))
idx=rot.get("cursor",0)%len(sched)
name=None
for step in range(len(sched)):              # first UNLEASED module from the cursor
    cand = mods[sched[(idx+step)%len(sched)][1]]["name"]
    if cand not in leases:
        name = cand; idx = (idx+step)%len(sched); break
if name is None:
    hist("no_claimable", pending=0)
    print(json.dumps(dict(common, mode="NO_CLAIMABLE", module=None, item_id=None, item=None))); sys.exit(0)
rot["cursor"]=(idx+1)%len(sched); atomic(c)
take_lease(name, None)
print(json.dumps(dict(common, mode="ROTATION", module=name, item_id=None, item=None)))
PYEOF
)
flock -u 221 || true

MODE=$(jq -r '.mode // ""' <<<"$PICK" 2>/dev/null || echo "")
TARGET=$(jq -r '.module // ""' <<<"$PICK" 2>/dev/null || echo "")
CAMPAIGN_ITEM_ID=$(jq -r '.item_id // ""' <<<"$PICK" 2>/dev/null || echo "")
CAMPAIGN_ITEM_JSON=$(jq -c '.item // {}' <<<"$PICK" 2>/dev/null || echo "{}")
PENDING_COUNT=$(jq -r '.pending // 0' <<<"$PICK" 2>/dev/null || echo 0)
# The item is the authority on which obligation this fire serves. The agent
# also echoes it back; write_summary records both so a mismatch is visible.
DIRECTIVE_REF=$(jq -c '.item.directive_ref // {}' <<<"$PICK" 2>/dev/null || echo "{}")
RESERVED_JSON=$(jq -c '.reserved // []' <<<"$PICK" 2>/dev/null || echo "[]")
OWNER_SKIPPED=$(jq -r '(.owner_skipped // []) | join(", ")' <<<"$PICK" 2>/dev/null || echo "")
EMPTY_MODULES=$(jq -r '(.empty_modules // []) | join(", ")' <<<"$PICK" 2>/dev/null || echo "")
LOW_MODULES=$(jq -r '(.low_modules // []) | join(", ")' <<<"$PICK" 2>/dev/null || echo "")
DIRECTIVE_OBL=$(jq -r '.item.directive_ref.item_id // ""' <<<"$PICK" 2>/dev/null || echo "")
DIRECTIVE_DOC=$(jq -r '.item.directive_ref.doc // ""' <<<"$PICK" 2>/dev/null || echo "")
LEASED_SKIPPED=$(jq -r '(.leased_skipped // []) | join(", ")' <<<"$PICK" 2>/dev/null || echo "")
CHAIN_ALERT=$(jq -r '.chain_alert // ""' <<<"$PICK" 2>/dev/null || echo "")

# --- directive routing (v5): item's doc -> registry -> index -----------------
DIRECTIVE_UNREGISTERED=0
if [ -n "$DIRECTIVE_DOC" ]; then
    IDX_REL=$(jq -r --arg d "$DIRECTIVE_DOC" '.directives[$d].index_path // ""' "$DIRECTIVE_REGISTRY" 2>/dev/null || echo "")
    if [ -n "$IDX_REL" ] && [ -f "$ROOT/$IDX_REL" ]; then
        DIRECTIVE_INDEX="$ROOT/$IDX_REL"
    else
        DIRECTIVE_UNREGISTERED=1
        echo "[$(date -Iseconds)] DIRECTIVE_UNREGISTERED: item $CAMPAIGN_ITEM_ID cites doc '$DIRECTIVE_DOC' which the registry does not know — verdicts on this item are blocked (fail closed)" >> "$LOG"
    fi
fi
REFUT_CRITERION=""
if [ -n "$DIRECTIVE_OBL" ] && [ -n "$DIRECTIVE_INDEX" ] && [ -f "$DIRECTIVE_INDEX" ]; then
    REFUT_CRITERION=$(jq -r --arg id "$DIRECTIVE_OBL" \
        '.obligations[]|select(.id==$id)|.refutation_criterion // ""' "$DIRECTIVE_INDEX" 2>/dev/null || echo "")
fi
if [ -n "$OWNER_SKIPPED" ]; then echo "[$(date -Iseconds)] OWNER_GUARD_SKIP: refused to dispatch human/lab-owned item(s): $OWNER_SKIPPED — these are founder or lab obligations; the loop files and tracks them, never executes them" >> "$LOG"; fi
if [ -n "$EMPTY_MODULES" ]; then echo "[$(date -Iseconds)] MODULE_EMPTY: no pending work for: $EMPTY_MODULES — these modules make no progress until refilled" >> "$LOG"; fi
if [ -n "$LOW_MODULES" ]; then echo "[$(date -Iseconds)] BACKLOG_LOW: one pending item left for: $LOW_MODULES" >> "$LOG"; fi
if [ -n "$LEASED_SKIPPED" ]; then echo "[$(date -Iseconds)] LEASE_SKIP: item(s) whose module a sibling lane holds: $LEASED_SKIPPED" >> "$LOG"; fi
if [ -n "$CHAIN_ALERT" ]; then
    A="[$(date -Iseconds)] ALERT CAMPAIGN_CHAIN: $CHAIN_ALERT"
    echo "$A" >> "$LOG"; mirror_line "$A"
    hb_event campaign_chain_alert ""
fi

if [ "$MODE" = "NO_CLAIMABLE" ]; then
    S="[$(date -Iseconds)] NO_CLAIMABLE: pending work exists but every claimable module is leased to a sibling lane — declining this slot"
    echo "$S" >> "$LOG"
    skip_record NO_CLAIMABLE_SKIP "all claimable modules leased"
    exit 0
fi

if [ "$MODE" = "ERROR" ] || [ -z "$TARGET" ]; then
    E="[$(date -Iseconds)] ERROR: cannot pick target: $(jq -r '.error // "no target"' <<<"$PICK" 2>/dev/null)"
    echo "$E" >> "$LOG"; mirror_line "$E"; exit 1
fi

# --- G3 directive drift (v5: scoped to the PICKED ITEM's document) -----------
# The document hash lives in the index and in every campaign item's
# directive_ref. Fail closed on mismatch: a fire must not bank a verdict
# against a document it cannot prove it is reading. Scoping matters under two
# directives: one stale document must block ITS items loudly, not freeze the
# other program's entirely.
DIRECTIVE_SHA=""
DIRECTIVE_MD=""
DIRECTIVE_DRIFT=NONE      # item carries no directive_ref: nothing to drift
if [ "$DIRECTIVE_UNREGISTERED" -eq 1 ]; then
    DIRECTIVE_DRIFT=UNREGISTERED
elif [ -n "$DIRECTIVE_INDEX" ]; then
    DIRECTIVE_SHA=$(jq -r '.directive.md_sha256 // ""' "$DIRECTIVE_INDEX" 2>/dev/null || echo "")
    DIRECTIVE_MD=$(jq -r '.directive.md_path // ""' "$DIRECTIVE_INDEX" 2>/dev/null || echo "")
    DIRECTIVE_DRIFT=UNKNOWN
    if [ -n "$DIRECTIVE_SHA" ] && [ -n "$DIRECTIVE_MD" ]; then
        LIVE_DIRECTIVE_SHA=$($SSH "$XBABE2_HOST" "sha256sum '$XBABE2_ROOT/$DIRECTIVE_MD' 2>/dev/null | cut -d' ' -f1" 2>/dev/null || echo "")
        if [ -z "$LIVE_DIRECTIVE_SHA" ]; then
            DIRECTIVE_DRIFT=UNREACHABLE
            echo "[$(date -Iseconds)] WARN: could not hash the directive on xbabe2 ($DIRECTIVE_MD)" >> "$LOG"
        elif [ "$LIVE_DIRECTIVE_SHA" != "$DIRECTIVE_SHA" ]; then
            DIRECTIVE_DRIFT=MISMATCH
            echo "[$(date -Iseconds)] DIRECTIVE_DRIFT[$DIRECTIVE_DOC]: index says $DIRECTIVE_SHA but the live document on xbabe2 hashes to $LIVE_DIRECTIVE_SHA — that directive has been superseded or altered; verdicts on ITS items are blocked until its index and their directive_refs are refreshed" >> "$LOG"
            mirror_line "[$(date -Iseconds)] ALERT DIRECTIVE_DRIFT[$DIRECTIVE_DOC] — verdicts on its items blocked"
        else
            DIRECTIVE_DRIFT=OK
        fi
    fi
fi

# --- A1: TARGET must be a plain module name. Nothing else may reach a shell --
if ! [[ "$TARGET" =~ ^amphora-[a-z0-9-]+$ ]]; then
    E="[$(date -Iseconds)] ERROR: refusing malformed target (possible injection): $TARGET"
    echo "$E" >> "$LOG"; mirror_line "$E"
    # Serialize when possible, but NEVER skip a hard stop for a lock.
    state_lock || true
    echo "$SATURATION_THRESHOLD" > "$NO_PROGRESS_FILE"
    printf 'MALFORMED_TARGET %s %s\n' "$(date -Iseconds)" "$TARGET" > "$HARD_STOP_FILE"
    state_unlock
    exit 1
fi

# backlog-low warning so the queue never silently empties again
if [ "$MODE" = "CAMPAIGN" ] && [ "$PENDING_COUNT" -lt 2 ]; then
    S="[$(date -Iseconds)] WARN BACKLOG_LOW: only $PENDING_COUNT pending campaign item(s) left"
    echo "$S" >> "$LOG"; mirror_line "$S"
elif [ "$MODE" = "ROTATION" ]; then
    S="[$(date -Iseconds)] WARN BACKLOG_EMPTY: no pending campaign items; running undirected rotation on $TARGET"
    echo "$S" >> "$LOG"; mirror_line "$S"
fi

RUN_START_BYTES=$(stat -c %s "$LOG")
RUN_START_EPOCH=$(date +%s)
RUN_START_ISO=$(date -Iseconds)
FIRE_PROMPT=$(mktemp /tmp/amphora-cron-prompt.XXXXXX.txt)
SNAP_PRE=$(mktemp /tmp/amphora-snap-pre.XXXXXX.json)
VERIFY_OUT=$(mktemp /tmp/amphora-verify.XXXXXX.json)
PROT_PRE=$(mktemp /tmp/amphora-prot-pre.XXXXXX)
PROT_POST=$(mktemp /tmp/amphora-prot-post.XXXXXX)

TARGET="$TARGET" MODE="$MODE" CAMPAIGN_ITEM_JSON="$CAMPAIGN_ITEM_JSON" MODEL="$MODEL" \
FIRE_ID="$FIRE_ID" RESERVED="$RESERVED_JSON" DIRECTIVE_SHA256="$DIRECTIVE_SHA" \
DIRECTIVE_ID="${DIRECTIVE_DOC:-none}" DIRECTIVE_MD_PATH="${DIRECTIVE_MD:-none}" \
python3 - "$PROMPT_TEMPLATE" "$FIRE_PROMPT" <<'PYEOF'
import os, sys
tpl = open(sys.argv[1]).read()
for ph, env in (("{{TARGET_MODULE}}","TARGET"), ("{{MODE}}","MODE"),
                ("{{CAMPAIGN_ITEM_JSON}}","CAMPAIGN_ITEM_JSON"), ("{{MODEL}}","MODEL"),
                ("{{FIRE_ID}}","FIRE_ID"), ("{{RESERVED_PATHS}}","RESERVED"),
                ("{{DIRECTIVE_SHA256}}","DIRECTIVE_SHA256"),
                ("{{DIRECTIVE_ID}}","DIRECTIVE_ID"),
                ("{{DIRECTIVE_MD_PATH}}","DIRECTIVE_MD_PATH")):
    tpl = tpl.replace(ph, os.environ.get(env, ""))
open(sys.argv[2],"w").write(tpl)
PYEOF

# --- A2 pre-fire: content-hash snapshot of the target module ----------------
# A4: if this fails we record it and BLOCK verdict acceptance later.
SNAP_OK=0
SNAP_PARAMS=$(python3 -c "
import json,base64,sys
print(base64.b64encode(json.dumps({'mode':'snapshot','root':sys.argv[1],
      'module':sys.argv[2],'ledger_path':sys.argv[3]}).encode()).decode())" \
    "$XBABE2_ROOT" "$TARGET" "$LEDGER")
if $SSH "$XBABE2_HOST" "python3 - $SNAP_PARAMS" < "$REMOTE_VERIFY" > "$SNAP_PRE" 2>/dev/null \
   && jq -e '.check == "OK"' "$SNAP_PRE" >/dev/null 2>&1; then
    SNAP_OK=1
    LEDGER_PRE=$(jq -r '.ledger_lines // 0' "$SNAP_PRE")
    # --- G1: the ledger is the evidence of record and is append-only by rule,
    # --- but nothing proved it. Hash the current content; post-fire the same
    # --- prefix must still hash identically, so history cannot be rewritten.
    LEDGER_PRE_SHA=$($SSH "$XBABE2_HOST" "head -n $LEDGER_PRE '$LEDGER' 2>/dev/null | sha256sum | cut -d\" \" -f1" 2>/dev/null || echo "")
else
    LEDGER_PRE=0
    LEDGER_PRE_SHA=""
    echo "[$(date -Iseconds)] WARN: pre-fire snapshot unavailable — verdicts will be blocked (fail closed)" >> "$LOG"
fi
# --- A7 protected files, tiered ---------------------------------------------
# IMMUTABLE: cron-owned + master manifest -> tamper => HARD_STOP
# COLLABORATIVE: mission.md files -> log only (a concurrent agent legitimately
# edits these; freezing the loop on that was a live near-miss).
# campaign.json is NOT here (v5): the loop is designed to write it, so under
# lanes a sibling's legitimate update inside this fire's PRE->POST window read
# as tamper and hard-stopped the whole fleet. Its integrity moved to the
# campaign hash chain in the lease history, plus git and the audit mirror.
snapshot_immutable() {
    # The registry plus EVERY registered index -- derived from the registry so
    # adding a directive extends the baseline automatically. Paths are loaded
    # into an array so even a future index name containing spaces stays atomic.
    local -a directive_indexes=()
    mapfile -t directive_indexes < <(
        jq -r '.directives[].index_path' "$DIRECTIVE_REGISTRY" 2>/dev/null \
          | sed "s|^|$CONTROLLER_ROOT/|" | sort)
    { sha256sum "$CONTROLLER_ROOT/claude-hourly-loop.sh" "$PROMPT_TEMPLATE" "$REMOTE_VERIFY" \
                "$DIRECTIVE_REGISTRY" "${directive_indexes[@]}" \
                2>/dev/null \
        | awk '{print $1"  xbabe1:"$2}'
      $SSH "$XBABE2_HOST" "sha256sum '$MASTER_MANIFEST' 2>/dev/null" \
        | awk -v host="$XBABE2_HOST" '{print $1"  "host":"$2}'
    } | sort -k2
}
PROT_BASELINE=OK
snapshot_immutable > "$PROT_PRE" || PROT_BASELINE=NOBASELINE
grep -Fq "$XBABE2_HOST:" "$PROT_PRE" 2>/dev/null || PROT_BASELINE=NOBASELINE
[ "$PROT_BASELINE" = NOBASELINE ] && \
    echo "[$(date -Iseconds)] WARN: protected baseline incomplete — verdicts will be blocked (fail closed)" >> "$LOG"

cd "$ROOT"

# --- fire --------------------------------------------------------------------
{
    echo ""
    echo "=================================================================="
    echo "=== $RUN_START_ISO START pid=$$ lane=$LANE host=$(hostname) target=$TARGET model=$MODEL mode=$MODE item=${CAMPAIGN_ITEM_ID:-none} fire_id=$FIRE_ID ==="
    echo "=================================================================="
    echo "campaign_pending: $PENDING_COUNT  snapshot_ok: $SNAP_OK  protected_baseline: $PROT_BASELINE  directive: $DIRECTIVE_DRIFT"
    echo "no_progress_count_pre_fire: $NO_PROGRESS"
    echo ""
    # `set +e` does NOT suppress an ERR trap, so the v3 sandwich fired on_err on
    # every non-zero agent exit and logged "FATAL ... post-processing aborted"
    # while post-processing in fact ran to completion -- three usage-limit
    # refusals looked like three script crashes. A command on the left of `||`
    # is exempt from ERR, so this form reports rc without the false alarm.
    # Lock fds are CLOSED for the agent: a process the agent leaves behind must
    # not inherit a lane slot or the fleet share -- capacity rides on the flocks,
    # module safety rides on the lease, and only the lease should outlive us.
    rc=0
    timeout --foreground --kill-after=30s "${MAX_SECS}s" \
        "$CLAUDE_BIN" --model "$MODEL" --permission-mode plan --dangerously-skip-permissions -p \
        < "$FIRE_PROMPT" {SLOT_FD}>&- {FLEET_FD}>&- 220>&- 221>&- || rc=$?
    echo ""
    echo "=================================================================="
    echo "=== $(date -Iseconds) END exit=$rc target=$TARGET fire_id=$FIRE_ID ==="
    echo "=================================================================="
} >> "$LOG" 2>&1

RUNTIME=$(( $(date +%s) - RUN_START_EPOCH ))

# --- lease renewal: the post-fire phase has no deadline of its own -----------
# ~8 serial ssh round-trips follow; renew before starting them so a slow remote
# cannot let the lease expire while this lane is still the module's writer.
if flock -w 30 221; then
    LANE="$LANE" FIRE_ID="$FIRE_ID" LEASE_TTL="$LEASE_TTL" \
    python3 - "$LANE_LEDGER" <<'PYEOF' >> "$LOG" 2>&1 || true
import json, os, sys, tempfile, datetime
path = sys.argv[1]
try:
    with open(path) as fh: ledger = json.load(fh)
except (FileNotFoundError, ValueError):
    sys.exit(0)
now_epoch = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
for mod, lease in (ledger.get("leases") or {}).items():
    if lease.get("fire_id") == os.environ["FIRE_ID"]:
        lease["expires"] = now_epoch + int(os.environ["LEASE_TTL"])
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".lane-ledger.")
        with os.fdopen(fd, "w") as fh:
            json.dump(ledger, fh, indent=2); fh.write("\n")
        os.replace(tmp, path)
        break
PYEOF
    flock -u 221 || true
fi

# --- parse the agent's summary ----------------------------------------------
FIRE_SLICE=$(tail -c +$((RUN_START_BYTES + 1)) "$LOG" 2>/dev/null || true)
SUMMARY_LINE=$(grep -a '^RUN_SUMMARY_JSON: ' <<<"$FIRE_SLICE" | tail -1 | sed 's/^RUN_SUMMARY_JSON: //' || true)
SUMMARY_OK=0
if [ -z "$SUMMARY_LINE" ] || ! jq -e . >/dev/null 2>&1 <<<"$SUMMARY_LINE"; then
    SUMMARY_LINE='{}'
    NOTES="no RUN_SUMMARY_JSON emitted"
else
    SUMMARY_OK=1
    NOTES=$(jq -r '.notes // ""' <<<"$SUMMARY_LINE")
fi

# --- fire classification -----------------------------------------------------
# The saturation gate exists to stop the loop when the PORTFOLIO is exhausted.
# It must never trip because the AGENT was. On 2026-08-06 three usage-limit
# refusals were counted as three exhausted hours and cost 80 hours of stall.
# Decide, before any counter moves, whether this fire ran and learned nothing
# (OK -- epistemic, the gate's business) or never ran at all (everything else).
FIRE_CLASS=OK
QUOTA_RESET_RAW=""
# QUOTA is the exhausted ACCOUNT window and holds the whole fleet -- so it must
# only match the CLI's own refusal (rc != 0 guards an agent merely quoting the
# words). A bare "rate limit" is a transient per-minute 429: real, but a
# fleet-wide multi-hour hold for a 60-second throttle would be self-harm, so it
# classifies as this lane's INFRA and the lane simply tries again next tick.
if [ "$rc" -ne 0 ] && grep -qaiE "hit your (weekly|usage|[0-9]+-hour) limit|usage limit reached" <<<"$FIRE_SLICE"; then
    FIRE_CLASS=QUOTA
    QUOTA_RESET_RAW=$(grep -aoiE "resets[^|]{0,40}" <<<"$FIRE_SLICE" | head -1 || true)
elif [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
    FIRE_CLASS=TIMEOUT
elif [ "$rc" -ne 0 ] && grep -qaiE "rate.?limit" <<<"$FIRE_SLICE"; then
    FIRE_CLASS=INFRA
elif [ "$rc" -ne 0 ] && [ "$SUMMARY_OK" -eq 0 ]; then
    FIRE_CLASS=INFRA
fi

if [ "$FIRE_CLASS" = QUOTA ]; then
    QPARSE=$(QUOTA_FALLBACK_SECS="$QUOTA_FALLBACK_SECS" QUOTA_HOLD_MAX="$QUOTA_HOLD_MAX" \
             python3 "$ROOT/lib/parse_quota_reset.py" "$QUOTA_RESET_RAW" 2>/dev/null || true)
    QUOTA_UNTIL_NEW=${QPARSE%% *}; QUOTA_HOW=${QPARSE#* }
    [[ "$QUOTA_UNTIL_NEW" =~ ^[0-9]+$ ]] || {
        QUOTA_UNTIL_NEW=$(( $(date +%s) + QUOTA_FALLBACK_SECS )); QUOTA_HOW=parser-unavailable; }
    # Fleet-global state; only ever EXTEND under the lock -- lane B's fresher
    # parse must not be clobbered by lane A's shorter one. On lock timeout,
    # do NOT mutate unlocked (review finding): retry longer, then skip loudly.
    if state_lock || flock -w 120 220; then
        if [ "$QUOTA_UNTIL_NEW" -gt "$(read_num "$QUOTA_HOLD_FILE")" ]; then
            echo "$QUOTA_UNTIL_NEW" > "$QUOTA_HOLD_FILE"
        fi
        state_unlock
    else
        echo "[$(date -Iseconds)] ALERT STATE_LOCK_TIMEOUT: quota hold NOT extended (fire_id=$FIRE_ID)" >> "$LOG"
        hb_event state_lock_timeout '"where":"quota-extend"'
    fi
    Q="[$(date -Iseconds)] QUOTA_DETECTED: usage limit hit (\"${QUOTA_RESET_RAW:-no reset time in message}\", parsed=$QUOTA_HOW) — holding fires until $(date -Iseconds -d "@$QUOTA_UNTIL_NEW"); NOT counted against saturation"
    echo "$Q" >> "$LOG"; mirror_line "$Q"
elif [ "$FIRE_CLASS" != OK ]; then
    echo "[$(date -Iseconds)] INFRA_FAIL[$FIRE_CLASS]: the agent produced no result (agent_rc=$rc, runtime=${RUNTIME}s) — infrastructure, not saturation" >> "$LOG"
fi
OUTCOME=$(jq -r '.outcome // "UNKNOWN"' <<<"$SUMMARY_LINE")
ARTIFACTS_JSON=$(jq -c '.artifacts // []' <<<"$SUMMARY_LINE")
VERDICT_SUMMARY=$(jq -r '.verdict_summary // ""' <<<"$SUMMARY_LINE")
RPT_ITEM_ID=$(jq -r '.campaign_item_id // ""' <<<"$SUMMARY_LINE")
RPT_ITEM_STATUS=$(jq -r '.campaign_item_status // ""' <<<"$SUMMARY_LINE")
case "$OUTCOME" in
    CLAIM_REFUTED|CLAIM_SURVIVED|BLOCKED_DATA|BLOCKED_RIGHTS|SATURATED|ERROR|UNKNOWN) : ;;
    *) OUTCOME="UNKNOWN" ;;
esac

# --- G1 append-only ledger verify --------------------------------------------
# A fire may only APPEND. If the first $LEDGER_PRE lines no longer hash to what
# they hashed pre-fire, history was rewritten or truncated: hard stop.
if [ -n "$LEDGER_PRE_SHA" ]; then
    LEDGER_POST_SHA=$($SSH "$XBABE2_HOST" "head -n $LEDGER_PRE '$LEDGER' 2>/dev/null | sha256sum | cut -d\" \" -f1" 2>/dev/null || echo "")
    if [ -z "$LEDGER_POST_SHA" ]; then
        echo "[$(date -Iseconds)] WARN: ledger append-only check unreachable" >> "$LOG"
    elif [ "$LEDGER_PRE_SHA" != "$LEDGER_POST_SHA" ]; then
        { echo "[$(date -Iseconds)] LEDGER_REWRITTEN (target=$TARGET fire_id=$FIRE_ID) — hard-stopping."
          echo "  first $LEDGER_PRE lines: pre=$LEDGER_PRE_SHA post=$LEDGER_POST_SHA"; } >> "$LOG"
        state_lock || true    # serialize if we can; never skip a hard stop
        echo "$SATURATION_THRESHOLD" > "$NO_PROGRESS_FILE"
        printf 'LEDGER_REWRITTEN %s fire_id=%s pre=%s post=%s\n' \
            "$(date -Iseconds)" "$FIRE_ID" "$LEDGER_PRE_SHA" "$LEDGER_POST_SHA" > "$HARD_STOP_FILE"
        state_unlock
        mirror_line "[$(date -Iseconds)] ALERT LEDGER_REWRITTEN fire_id=$FIRE_ID — loop hard-stopped"
    fi
fi

# --- A7 protected verify -----------------------------------------------------
PROTECTED_CHECK=OK
if [ "$PROT_BASELINE" = NOBASELINE ]; then
    PROTECTED_CHECK=NOBASELINE
elif ! snapshot_immutable > "$PROT_POST" 2>/dev/null || ! grep -Fq "$XBABE2_HOST:" "$PROT_POST"; then
    PROTECTED_CHECK=FAILED
    echo "[$(date -Iseconds)] WARN: post-fire protected check unreachable" >> "$LOG"
elif ! PROT_DIFF=$(diff "$PROT_PRE" "$PROT_POST"); then
    PROTECTED_CHECK=MODIFIED
    { echo "[$(date -Iseconds)] PROTECTED_FILE_MODIFIED (target=$TARGET fire_id=$FIRE_ID) — hard-stopping:"
      printf '%s\n' "$PROT_DIFF"; } >> "$LOG"
    state_lock || true    # serialize if we can; never skip a hard stop
    echo "$SATURATION_THRESHOLD" > "$NO_PROGRESS_FILE"
    printf 'PROTECTED_FILE_MODIFIED %s fire_id=%s\n%s\n' "$(date -Iseconds)" "$FIRE_ID" "$PROT_DIFF" > "$HARD_STOP_FILE"
    state_unlock
    mirror_line "[$(date -Iseconds)] ALERT PROTECTED_FILE_MODIFIED fire_id=$FIRE_ID — loop hard-stopped"
fi

# --- A2/A3/A6 identity-bound verification -----------------------------------
SIGNING_CHECK=FAILED; VERIFIED_NEW_SIGNED=0; SIGNING_VIOLATIONS=0; LEDGER_FIREID=false
PC_OK=true; PC_REASON=""; PC_DOWNGRADE=0
DC_OK=true; DC_REASON=""
if [ "$SNAP_OK" -eq 1 ]; then
    VPARAMS=$(python3 -c "
import json,base64,sys
snap=json.load(open(sys.argv[4])).get('snapshot',{})
print(base64.b64encode(json.dumps({'mode':'verify','root':sys.argv[1],'module':sys.argv[2],
  'fire_id':sys.argv[3],'ledger_path':sys.argv[5],'pre_snapshot':snap,
  'declared_artifacts':json.loads(sys.argv[6]),'outcome':sys.argv[7],
  'directive_ref':json.loads(sys.argv[8] or '{}'),
  'refutation_criterion':sys.argv[9], 'signing_key_path':sys.argv[10]}).encode()).decode())" \
        "$XBABE2_ROOT" "$TARGET" "$FIRE_ID" "$SNAP_PRE" "$LEDGER" "$ARTIFACTS_JSON" "$OUTCOME" \
        "$DIRECTIVE_REF" "$REFUT_CRITERION" "$SIGNING_KEY_PATH")
    if $SSH "$XBABE2_HOST" "python3 - $VPARAMS" < "$REMOTE_VERIFY" > "$VERIFY_OUT" 2>/dev/null \
       && jq -e '.check == "OK"' "$VERIFY_OUT" >/dev/null 2>&1; then
        SIGNING_CHECK=OK
        VERIFIED_NEW_SIGNED=$(jq -r '.verified_new_signed // 0' "$VERIFY_OUT")
        SIGNING_VIOLATIONS=$(jq -r '.signing_violations_in_module // 0' "$VERIFY_OUT")
        LEDGER_FIREID=$(jq -r '.ledger_has_fire_id // false' "$VERIFY_OUT")
        PC_OK=$(jq -r '.positive_control.ok // true' "$VERIFY_OUT")
        PC_REASON=$(jq -r '.positive_control.reason // ""' "$VERIFY_OUT")
        DC_OK=$(jq -r '.directive_citation.ok // true' "$VERIFY_OUT")
        DC_REASON=$(jq -r '.directive_citation.reason // ""' "$VERIFY_OUT")
        if [ "$SIGNING_VIOLATIONS" -gt 0 ]; then
            { echo "[$(date -Iseconds)] SIGNING_VIOLATION: $SIGNING_VIOLATIONS declared artifact(s) failed DSSE verification (target=$TARGET):"
              jq -r '.rejected[]? | "    " + .path + " (" + .reason + ")"' "$VERIFY_OUT"; } >> "$LOG"
        fi
    else
        echo "[$(date -Iseconds)] WARN: remote verification failed — signing_check=FAILED (fail closed)" >> "$LOG"
    fi
fi

# --- A4 anti-gaming: verdicts require verified evidence ----------------------
OUTCOME_RAW="$OUTCOME"; DOWNGRADE_REASON=""
case "$OUTCOME" in
  CLAIM_REFUTED|CLAIM_SURVIVED)
      if [ "$SIGNING_CHECK" != OK ] || [ "${VERIFIED_NEW_SIGNED:-0}" -eq 0 ] \
         || [ "$LEDGER_FIREID" != true ] || [ "$PROTECTED_CHECK" = NOBASELINE ] \
         || [ "$DIRECTIVE_DRIFT" = MISMATCH ] || [ "$DIRECTIVE_DRIFT" = UNREGISTERED ]; then
          OUTCOME=UNKNOWN
          DOWNGRADE_REASON="verdict $OUTCOME_RAW not accepted: signing_check=$SIGNING_CHECK, verified_new_signed=$VERIFIED_NEW_SIGNED (must be a DECLARED artifact that passes real Ed25519 DSSE verification against the pinned Phase-0 key), ledger_has_fire_id=$LEDGER_FIREID (the ledger line must carry fire_id=$FIRE_ID), protected_check=$PROTECTED_CHECK, directive_drift=$DIRECTIVE_DRIFT"
          echo "[$(date -Iseconds)] DOWNGRADE: $OUTCOME_RAW->UNKNOWN ($DOWNGRADE_REASON)" >> "$LOG"
      elif [ "$OUTCOME_RAW" = CLAIM_SURVIVED ] && [ "$PC_OK" != true ]; then
          # A survival must show a POSITIVE CONTROL: a defect deliberately planted
          # in the attack's own input, which the attack then detected. W-RTA2 proved
          # that without this, a deliberately weak attack passes every check and
          # licenses a survival. NOT counted against progress -- the fire did bank a
          # verified artifact; it simply has not earned the word SURVIVED.
          OUTCOME=UNKNOWN
          PC_DOWNGRADE=1
          DOWNGRADE_REASON="CLAIM_SURVIVED not accepted: $PC_REASON. A survival must carry positive_control{planted_defect, detected:true} in a credited receipt, showing the attack fired on a defect deliberately planted in its own input."
          echo "[$(date -Iseconds)] DOWNGRADE: CLAIM_SURVIVED->UNKNOWN (positive control: $PC_REASON)" >> "$LOG"
      elif [ "$DC_OK" != true ]; then
          # A verdict on a founder obligation must be BOUND to that obligation.
          # This was prose-only until now -- the same defect W-RTA2 proved for the
          # survival bar, reintroduced by the change meant to apply its lesson.
          # Non-saturating for the same reason as the positive control: the fire
          # did bank a verified artifact, it simply has not shown what it answers.
          OUTCOME=UNKNOWN
          PC_DOWNGRADE=1
          DOWNGRADE_REASON="verdict not accepted: $DC_REASON. A receipt for an item carrying a directive_ref must record directive_path, directive_sha256 and directive_obligation, and must restate the obligation's pre-committed refutation_criterion VERBATIM."
          echo "[$(date -Iseconds)] DOWNGRADE: $OUTCOME_RAW->UNKNOWN (directive citation: $DC_REASON)" >> "$LOG"
      fi ;;
  BLOCKED_DATA)
      # v5: keyed on THIS fire's id, not a before/after line count -- under
      # lanes a sibling's ask arriving in the window made any lane's unearned
      # BLOCKED_DATA pass. FIRE_ID is 128 bits of /dev/urandom; its presence in
      # the queue is this fire's append and nobody else's.
      if ! grep -qa "$FIRE_ID" "$DATA_ASK_QUEUE" 2>/dev/null; then
          OUTCOME=UNKNOWN
          DOWNGRADE_REASON="BLOCKED_DATA claimed but no data-acquisition-queue entry carries fire_id=$FIRE_ID (entries must include the fire_id field)"
          echo "[$(date -Iseconds)] DOWNGRADE: $DOWNGRADE_REASON" >> "$LOG"
      fi ;;
esac

# --- HARD_STOP re-check before anything is banked ----------------------------
# Two ways a stop can exist by now: a sibling lane tripped it mid-fire, or THIS
# fire's own ledger/protected checks wrote it above -- and v4 then banked the
# tripped fire's verdict anyway, a pre-existing hole. Either way: the fire
# record is preserved, the verdict is not, no status transition, no counters.
HARD_STOP_MIDFIRE=0
state_lock || true
if [ -f "$HARD_STOP_FILE" ]; then
    HARD_STOP_MIDFIRE=1
    OUTCOME=UNKNOWN
    DOWNGRADE_REASON="HARD_STOP present during fire ($( { head -1 "$HARD_STOP_FILE" 2>/dev/null || true; } | cut -c1-120)); verdict not banked"
    echo "[$(date -Iseconds)] HARD_STOP_MIDFIRE: banking UNKNOWN, suppressing status transitions" >> "$LOG"
fi
state_unlock

# --- counters (critical section, lock order position 4) ----------------------
# Two counters, never one. The saturation counter answers "is there anything
# left to learn here?" and only a fire that actually RAN may answer it. A fire
# that never ran answers a different question, on its own counter, with its own
# threshold -- so an outage can no longer masquerade as an exhausted portfolio.
# Both are RE-READ inside the lock: the pre-fire values are 10-55 minutes stale
# by now, and `echo $((stale+1))` from four lanes walks a counter BACKWARDS --
# three failures could record as one, and the gate would never trip.
GATE_CLEARED=0
if [ "$PROTECTED_CHECK" != MODIFIED ] && [ "$HARD_STOP_MIDFIRE" -eq 0 ]; then
  if ! state_lock && ! flock -w 120 220; then
    # Unlocked counter writes are the lost-update bug re-reading exists to
    # kill (review finding). Skip loudly; a skipped movement is visible, a
    # corrupted counter is not. The post-fire phase has no deadline, so the
    # long retry above is free.
    echo "[$(date -Iseconds)] ALERT STATE_LOCK_TIMEOUT: counters NOT moved for fire_id=$FIRE_ID (class=$FIRE_CLASS outcome=$OUTCOME)" >> "$LOG"
    hb_event state_lock_timeout '"where":"counters"'
  else
  INFRA_NOW=$(read_num "$INFRA_FAIL_FILE")
  SAT_NOW=$(read_num "$NO_PROGRESS_FILE")
  if [ "$FIRE_CLASS" != OK ]; then
      echo $(( INFRA_NOW + 1 )) > "$INFRA_FAIL_FILE"
      echo "[$(date -Iseconds)] COUNTERS: infra=$(( INFRA_NOW + 1 ))/$INFRA_THRESHOLD (class=$FIRE_CLASS), saturation left at $SAT_NOW/$SATURATION_THRESHOLD" >> "$LOG"
  else
      echo 0 > "$INFRA_FAIL_FILE"
      case "$OUTCOME" in
        CLAIM_REFUTED|CLAIM_SURVIVED) echo 0 > "$NO_PROGRESS_FILE"; GATE_CLEARED=1 ;;
        UNKNOWN)
            # A positive-control downgrade is not a wasted hour: the fire produced a
            # verified signed artifact. Do not let it drive the loop to saturation.
            if [ "${PC_DOWNGRADE:-0}" -eq 1 ]; then echo 0 > "$NO_PROGRESS_FILE"; GATE_CLEARED=1
            else echo $((SAT_NOW+1)) > "$NO_PROGRESS_FILE"; fi ;;
        BLOCKED_DATA|BLOCKED_RIGHTS)
            if [ "$MODE" = ROTATION ]; then echo $((SAT_NOW+1)) > "$NO_PROGRESS_FILE"; fi ;;
        *) echo $((SAT_NOW+1)) > "$NO_PROGRESS_FILE" ;;
      esac
  fi
  # Verified information ends a hold at any backoff level: the probe worked.
  if [ "$GATE_CLEARED" -eq 1 ]; then
      rm -f "$GATE_HOLD_FILE" "$GATE_LEVEL_FILE"
      clear_stall
  fi
  state_unlock
  fi
fi

# --- A5 campaign update + lease release (lock order position 3) ---------------
# The done_check is a remote call and runs BEFORE the lock; the read-modify-
# write of campaign.json and the lease ledger runs entirely inside it -- the v4
# update was last-replace-wins and under four lanes would have silently erased
# ~3 of 4 fire records per wave. Release is compare-and-delete on (module,
# fire_id): if the lease is not ours any more (TTL expired, sibling claimed the
# module), the fire record still lands but NO status transition applies -- the
# module has a new owner and this fire's word is no longer current.
ITEM_STATUS_APPLIED=none
DONE_CHECK_RC=skipped
if [ "$MODE" = CAMPAIGN ] && [ -n "$CAMPAIGN_ITEM_ID" ]; then
    if [ "$RPT_ITEM_STATUS" = "done" ] && [ "$RPT_ITEM_ID" = "$CAMPAIGN_ITEM_ID" ]; then
        DC_KIND=$(jq -r --arg id "$CAMPAIGN_ITEM_ID" \
            '.items[]|select(.id==$id)|.done_check|if type=="object" then (.kind//"") else "" end' "$CAMPAIGN")
        case "$DC_KIND" in
          signed_receipt_glob)
              DC_GLOB=$(jq -r --arg id "$CAMPAIGN_ITEM_ID" '.items[]|select(.id==$id)|.done_check.glob' "$CAMPAIGN")
              DCP=$(python3 -c "
import json,base64,sys
print(base64.b64encode(json.dumps({'mode':'donecheck','root':sys.argv[1],
      'module':sys.argv[2],'glob':sys.argv[3], 'signing_key_path':sys.argv[4]}).encode()).decode())" \
                  "$XBABE2_ROOT" "$TARGET" "$DC_GLOB" "$SIGNING_KEY_PATH")
              if $SSH "$XBABE2_HOST" "python3 - $DCP" < "$REMOTE_VERIFY" 2>/dev/null | jq -e '.pass == true' >/dev/null 2>&1
                 then DONE_CHECK_RC=pass; else DONE_CHECK_RC=fail; fi ;;
          *)  # A5: a string check, or none at all, BLOCKS done (v2 passed it)
              DONE_CHECK_RC=unverifiable ;;
        esac
    fi
fi
CAMPAIGN_LOCKED=1
if ! flock -w 30 221; then
    # One retry with a longer window, then say so LOUDLY -- and then actually
    # mean it: the first draft alerted "fire record NOT banked" and fell
    # through to bank it anyway, UNLOCKED, which is the exact lost-write bug
    # this lock exists to kill (caught by three review lenses independently).
    # The unreleased lease is fine: the TTL reap at claim time is the designed
    # self-heal for exactly this.
    if ! flock -w 120 221; then
        CAMPAIGN_LOCKED=0
        U="[$(date -Iseconds)] ALERT CAMPAIGN_UPDATE_LOST fire_id=$FIRE_ID item=$CAMPAIGN_ITEM_ID — campaign.lock not acquired; fire record NOT banked"
        echo "$U" >> "$LOG"; mirror_line "$U"; hb_event campaign_update_lost ""
    fi
fi
if [ "$CAMPAIGN_LOCKED" -eq 0 ]; then
    UPDATE_OUT='{"applied":"update-lost","lease":"unreleased-ttl-reap"}'
else
UPDATE_OUT=$(MODE="$MODE" OUTCOME="$OUTCOME" RPT_ID="$RPT_ITEM_ID" RPT_STATUS="$RPT_ITEM_STATUS" \
    PICKED_ID="$CAMPAIGN_ITEM_ID" DONE_CHECK_RC="$DONE_CHECK_RC" TS="$RUN_START_ISO" \
    VERDICT="$VERDICT_SUMMARY" NOTES="$NOTES" ARTIFACTS="$ARTIFACTS_JSON" \
    DOWNGRADE_REASON="$DOWNGRADE_REASON" FIRE_ID="$FIRE_ID" LANE="$LANE" \
    TARGET="$TARGET" SUPPRESS="${HARD_STOP_MIDFIRE:-0}" FIRE_CLASS="$FIRE_CLASS" \
    python3 - "$CAMPAIGN" "$LANE_LEDGER" "$LANE_HISTORY" <<'PYEOF' || echo '{"applied":"update-failed","lease":"unknown"}'
import hashlib, json, os, sys, tempfile
camp_path, ledger_path, hist_path = sys.argv[1], sys.argv[2], sys.argv[3]
env = os.environ

raw = open(camp_path, "rb").read()
pre_sha = hashlib.sha256(raw).hexdigest()
c = json.loads(raw)                            # re-read: honour edits made during the fire

def hist(event, **kw):
    rec = {"ts": env["TS"], "event": event, "lane": env["LANE"], "fire_id": env["FIRE_ID"]}
    rec.update(kw)
    with open(hist_path, "a") as fh:
        fh.write(json.dumps(rec) + "\n")

# Lease ownership decides whether this fire may still move statuses.
try:
    with open(ledger_path) as fh: ledger = json.load(fh)
except (FileNotFoundError, ValueError):
    ledger = {"leases": {}}
leases = ledger.setdefault("leases", {})
own = leases.get(env["TARGET"], {}).get("fire_id") == env["FIRE_ID"]
suppress = env.get("SUPPRESS") == "1" or not own

applied = "none"
if env["MODE"] == "CAMPAIGN" and env["PICKED_ID"]:
    applied = "pending"
    picked = env["PICKED_ID"]
    for item in c["items"]:
        if item["id"] != picked: continue
        fire = {"ts": env["TS"], "fire_id": env["FIRE_ID"], "lane": env["LANE"],
                "outcome": env["OUTCOME"], "fire_class": env.get("FIRE_CLASS", "OK"),
                "verdict_summary": env["VERDICT"][:400], "notes": env["NOTES"][:400]}
        if env.get("DOWNGRADE_REASON"): fire["downgrade_reason"] = env["DOWNGRADE_REASON"][:400]
        if not own: fire["lease_lost"] = True
        try: fire["artifacts"] = json.loads(env["ARTIFACTS"])[:20]
        except Exception: fire["artifacts"] = []
        item.setdefault("fires", []).append(fire)
        if suppress:
            applied = "pending"
            if env["RPT_STATUS"] == "done":
                fire["done_rejected"] = "transition suppressed (%s)" % ("lease_lost" if not own else "hard_stop_midfire")
        elif (env["RPT_STATUS"] == "done" and env["RPT_ID"] == picked
                and env["OUTCOME"] in ("CLAIM_REFUTED", "CLAIM_SURVIVED")
                and env["DONE_CHECK_RC"] == "pass"):
            item["status"] = "done"; applied = "done"
        elif env["RPT_STATUS"] == "blocked" and env["OUTCOME"] in ("BLOCKED_DATA", "BLOCKED_RIGHTS"):
            item["status"] = "blocked"; item["blocked_reason"] = env["NOTES"][:400]; applied = "blocked"
        else:
            applied = "pending"
            if env["RPT_STATUS"] == "done":
                fire["done_rejected"] = "outcome=%s done_check=%s" % (env["OUTCOME"], env["DONE_CHECK_RC"])
        break
    body = json.dumps(c, indent=2) + "\n"
    post_sha = hashlib.sha256(body.encode()).hexdigest()
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(camp_path), prefix=".campaign.")
    with os.fdopen(fd, "w") as fh: fh.write(body)
    os.replace(tmp, camp_path)
    hist("update", item_id=picked, applied=applied,
         campaign_pre_sha256=pre_sha, campaign_post_sha256=post_sha)

# Release: compare-and-delete on (module, fire_id). A foreign lease is a
# sibling's -- deleting it would re-open the module under them.
lease_state = "not-held"
if own:
    hist("release", module=env["TARGET"],
         item_id=leases[env["TARGET"]].get("item_id"), outcome=env["OUTCOME"])
    del leases[env["TARGET"]]
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ledger_path), prefix=".lane-ledger.")
    with os.fdopen(fd, "w") as fh:
        json.dump(ledger, fh, indent=2); fh.write("\n")
    os.replace(tmp, ledger_path)
    lease_state = "released"
elif env["TARGET"] in leases:
    hist("lease_lost", module=env["TARGET"], holder=leases[env["TARGET"]])
    lease_state = "lost-to-" + str(leases[env["TARGET"]].get("lane"))

print(json.dumps({"applied": applied, "lease": lease_state}))
PYEOF
)
flock -u 221 || true
fi
ITEM_STATUS_APPLIED=$(jq -r '.applied // "update-failed"' <<<"$UPDATE_OUT" 2>/dev/null || echo update-failed)
LEASE_STATE=$(jq -r '.lease // "unknown"' <<<"$UPDATE_OUT" 2>/dev/null || echo unknown)
if [ "$MODE" = CAMPAIGN ] && [ -n "$CAMPAIGN_ITEM_ID" ]; then
    echo "[$(date -Iseconds)] CAMPAIGN: item=$CAMPAIGN_ITEM_ID reported=$RPT_ITEM_STATUS done_check=$DONE_CHECK_RC applied=$ITEM_STATUS_APPLIED lease=$LEASE_STATE" >> "$LOG"
fi
case "$LEASE_STATE" in lost-*)
    L="[$(date -Iseconds)] LEASE_LOST: module $TARGET is leased to lane ${LEASE_STATE#lost-to-} — this fire's record was banked without status transitions"
    echo "$L" >> "$LOG"; mirror_line "$L"; hb_event lease_lost "" ;;
esac

# --- directive_ref echo check ------------------------------------------------
# write_summary records both the item's authoritative directive_ref and the
# agent's echo. Nothing read them until now, so the "a mismatch stays visible"
# claim was not actually true of anything.
DIRECTIVE_REF_ECHO=$(jq -c '.directive_ref // {}' <<<"$SUMMARY_LINE" 2>/dev/null || echo "{}")
if [ -n "$DIRECTIVE_OBL" ]; then
    ECHO_OBL=$(jq -r '.item_id // ""' <<<"$DIRECTIVE_REF_ECHO" 2>/dev/null || echo "")
    if [ -n "$ECHO_OBL" ] && [ "$ECHO_OBL" != "$DIRECTIVE_OBL" ]; then
        echo "[$(date -Iseconds)] DIRECTIVE_REF_MISMATCH: item was assigned obligation $DIRECTIVE_OBL but the fire reported $ECHO_OBL — the fire may have worked on something other than what it was given" >> "$LOG"
    fi
fi

# --- fast-fire flag (directive A.1 pre-commit) -------------------------------
# "A fire that finishes materially faster than the 8m55s median is opened for
# inspection before its verdict is banked." Median over 223 fires = 537s.
# LOG ONLY -- an unexplained fast fire is a smell, not proof, so it must never
# downgrade a verdict on its own; a human reads the flag.
if [ "${RUNTIME:-0}" -gt 0 ] && [ "${RUNTIME:-0}" -lt 268 ]; then
    echo "[$(date -Iseconds)] FAST_FIRE: runtime=${RUNTIME}s is under half the 537s median (item=$CAMPAIGN_ITEM_ID outcome=$OUTCOME) — inspect before trusting this verdict" >> "$LOG"
fi

# --- A10 summary record: agent JSON on STDIN (argv hit E2BIG in v2) ---------
printf '%s' "$SUMMARY_LINE" | python3 "$ROOT/lib/write_summary.py" \
        "$FIRE_SUMMARY" "$RUN_START_ISO" "$TARGET" "$MODE" "$MODEL" "$CAMPAIGN_ITEM_ID" \
        "$ITEM_STATUS_APPLIED" "$OUTCOME" "$OUTCOME_RAW" "$FIRE_ID" "$SIGNING_CHECK" \
        "$PROTECTED_CHECK" "$RUNTIME" "$VERIFIED_NEW_SIGNED" "$SIGNING_VIOLATIONS" \
        "$LEDGER_FIREID" "$DIRECTIVE_REF" "$rc" "$FIRE_CLASS" "$LANE" \
  || echo "{\"ts\":\"$RUN_START_ISO\",\"module\":\"$TARGET\",\"fire_id\":\"$FIRE_ID\",\"outcome\":\"SUMMARY_WRITE_FAIL\"}" >> "$FIRE_SUMMARY"

# --- audit mirror + prune -----------------------------------------------------
# v5: the per-fire log-slice push is gone -- mirror-log.sh rsyncs the per-lane
# logs on its own cadence, and a slice from a shared window duplicated sibling
# bytes up to 4x. Config push: compare-and-SET under the state lock (claim the
# sha before pushing so exactly one lane pushes a given state; delete the claim
# on failure so the next fire retries), scp from a snapshot taken OUTSIDE the
# lock, and stamp with the fire id -- two lanes finishing in the same second
# produced identical remote names and interleaved uploads.
CUR_SHA=$(sha256sum "$CONTROLLER_ROOT/claude-hourly-loop.sh" "$PROMPT_TEMPLATE" "$CAMPAIGN" 2>/dev/null | sha256sum | awk '{print $1}')
CLAIM_PUSH=0
if state_lock; then
    if [ "$CUR_SHA" != "$(cat "$MIRROR_SHA_FILE" 2>/dev/null || echo)" ]; then
        echo "$CUR_SHA" > "$MIRROR_SHA_FILE"
        CLAIM_PUSH=1
    fi
    state_unlock
fi   # on timeout: no claim, no push — the next fire retries; never mutate unlocked
if [ "$CLAIM_PUSH" -eq 1 ]; then
    STAMP="$(date +%Y%m%dT%H%M%S).$FIRE_ID"
    CAMP_SNAP=$(mktemp /tmp/amphora-campaign-snap.XXXXXX.json)
    cp "$CAMPAIGN" "$CAMP_SNAP" 2>/dev/null || true
    if $SSH "$XBABE2_HOST" "mkdir -p '$AUDIT_DIR'" >/dev/null 2>&1 \
       && scp -o ConnectTimeout=15 -o BatchMode=yes -q "$CONTROLLER_ROOT/claude-hourly-loop.sh" "$XBABE2_HOST:$AUDIT_DIR/claude-hourly-loop.sh.$STAMP" \
       && scp -o ConnectTimeout=15 -o BatchMode=yes -q "$PROMPT_TEMPLATE" "$XBABE2_HOST:$AUDIT_DIR/claude-hourly-loop.prompt.txt.$STAMP" \
       && scp -o ConnectTimeout=15 -o BatchMode=yes -q "$CAMP_SNAP" "$XBABE2_HOST:$AUDIT_DIR/campaign.json.$STAMP"; then
        echo "[$(date -Iseconds)] AUDIT_MIRROR: pushed *.$STAMP" >> "$LOG"
        $SSH "$XBABE2_HOST" "ls -1t '$AUDIT_DIR' | tail -n +$((AUDIT_KEEP+1)) | sed 's|^|$AUDIT_DIR/|' | xargs -r rm -f" >/dev/null 2>&1 || true
    else
        # Push failed: surrender the claim so a later fire retries.
        if state_lock; then
            if [ "$(cat "$MIRROR_SHA_FILE" 2>/dev/null || echo)" = "$CUR_SHA" ]; then rm -f "$MIRROR_SHA_FILE"; fi
            state_unlock
            echo "[$(date -Iseconds)] WARN: audit mirror push failed — claim surrendered for retry" >> "$LOG"
        else
            echo "[$(date -Iseconds)] WARN: audit mirror push failed AND claim not surrendered (state.lock timeout) — this config state stays unmirrored until the next config change" >> "$LOG"
        fi
    fi
    rm -f "$CAMP_SNAP" 2>/dev/null || true
fi

}
main "$@"
