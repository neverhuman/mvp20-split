#!/usr/bin/env bash
# T5-T8: backoff gate, probe release, alerting, and the 2026-08-06 regression.
set -uo pipefail
cd "$(dirname "$0")"; . ./harness.sh

QUOTA_MSG="You've hit your weekly limit · resets Aug 7, 12pm (UTC)"
DUD='RUN_SUMMARY_JSON: {"module":"amphora-rdkit-ffi","outcome":"UNKNOWN","artifacts":[],"receipts_added":0,"data_asks_added":0,"notes":"nothing found"}'
lastskip() { tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .outcome; }
expire_gate() { echo $(( $(date +%s) - 10 )) > "$SB/state/gate-hold-until"; }

echo "T5: saturation gate holds, then self-releases with doubling backoff"
sandbox_reset
fire 0 "$DUD"; fire 0 "$DUD"; fire 0 "$DUD"      # 3 fruitless OK fires -> trip
check "counter reached threshold"     "3"       "$(st consecutive-no-progress.txt)"
fire 0 "$DUD"                                    # 4th: gate trips + holds
check "gate now holding"              "SATURATION_SKIP" "$(lastskip)"
check "hold level 1"                  "1"       "$(st gate-hold-level)"
check "STALLED file written"          "SATURATION" "$(jq -r .kind "$SB/state/STALLED" 2>/dev/null)"
check "heartbeat carries stall event" "1"       "$(grep -c '"event":"stalled"' "$SB/logs/heartbeat.jsonl" || true)"

fire 0 "$DUD"                                    # still inside the hold
check "held fire did not run the agent" "SATURATION_SKIP" "$(lastskip)"
check "hold level unchanged"          "1"       "$(st gate-hold-level)"

expire_gate; fire 0 "$DUD"                       # probe, fruitless
check "probe actually ran"            "UNKNOWN" "$(lastskip)"
check "level doubled to 2"            "2"       "$(st gate-hold-level)"
check "re-latched immediately"        "3"       "$(st consecutive-no-progress.txt)"
next=$(st gate-hold-until); now=$(date +%s)
check "next hold is ~2h"              "yes"     "$([ $((next-now)) -gt 6000 ] && [ $((next-now)) -le 7200 ] && echo yes || echo no)"

expire_gate; fire 0 "$DUD"
check "level doubled to 3"            "3"       "$(st gate-hold-level)"
next=$(st gate-hold-until); now=$(date +%s)
check "next hold is ~4h"              "yes"     "$([ $((next-now)) -gt 13000 ] && [ $((next-now)) -le 14400 ] && echo yes || echo no)"

echo
echo "T5b: backoff saturates at the 24h ceiling instead of growing without bound"
echo 9 > "$SB/state/gate-hold-level"; expire_gate; fire 0 "$DUD"
next=$(st gate-hold-until); now=$(date +%s)
check "hold clamped to 24h"           "yes" "$([ $((next-now)) -gt 86000 ] && [ $((next-now)) -le 86400 ] && echo yes || echo no)"
echo 19 > "$SB/state/gate-hold-level"; expire_gate; fire 0 "$DUD"
check "level stops at the cap"        "20"  "$(st gate-hold-level)"
next=$(st gate-hold-until); now=$(date +%s)
check "still 24h, no overflow"        "yes" "$([ $((next-now)) -gt 86000 ] && [ $((next-now)) -le 86400 ] && echo yes || echo no)"
echo 20 > "$SB/state/gate-hold-level"; expire_gate; fire 0 "$DUD"
check "level does not exceed the cap"  "20" "$(st gate-hold-level)"

echo
echo "T6: a manual unblock clears every hold artefact"
echo 0 > "$SB/state/consecutive-no-progress.txt"
fire 0 "$DUD"
check "no stale hold-until inherited" "-"       "$(st gate-hold-until)"
check "no stale level inherited"      "-"       "$(st gate-hold-level)"
check "STALLED cleared"               "no"      "$([ -f "$SB/state/STALLED" ] && echo yes || echo no)"
check "RECOVERED logged"              "1"       "$(grep -ac 'RECOVERED: stall cleared' "$(lanelog 1)" || true)"

echo
echo "T7: the infra gate has its own threshold and never reads as saturation"
sandbox_reset
for _ in 1 2 3 4 5; do fire 1 "$QUOTA_MSG"; rm -f "$SB/state/quota-hold-until"; done
check "5 infra fails, gate still open" "5"      "$(st consecutive-infra-fail.txt)"
check "saturation untouched by all 5"  "0"      "$(st consecutive-no-progress.txt)"
fire 1 "$QUOTA_MSG"; rm -f "$SB/state/quota-hold-until"
fire 1 "$QUOTA_MSG"
check "6th trips the INFRA gate"       "INFRA_SKIP" "$(lastskip)"
check "and it is labelled INFRA"       "INFRA"      "$(jq -r .kind "$SB/state/STALLED" 2>/dev/null)"

echo
echo "T8: REGRESSION — the exact 2026-08-06 sequence cannot latch the loop again"
sandbox_reset
fire 1 "$QUOTA_MSG"          # 10:00
fire 1 "$QUOTA_MSG"          # 11:00
fire 1 "$QUOTA_MSG"          # 12:00
check "saturation counter still 0"     "0"     "$(st consecutive-no-progress.txt)"
fire 0 "$DUD"                # 13:00 — in v3 this hour was SATURATED_SKIP
check "13:00 is a quota hold, not saturation" "QUOTA_HOLD" "$(lastskip)"
check "no SATURATION_SKIP anywhere"    "0"     "$(grep -ac 'SATURATION_SKIP' "$(lanelog 1)" || true)"
# ... and once the stated reset passes, the loop resumes with no human action
echo $(( $(date +%s) - 10 )) > "$SB/state/quota-hold-until"
fire 0 "$DUD"
check "auto-resumes after the reset"   "UNKNOWN" "$(lastskip)"
check "quota hold file removed"        "-"       "$(st quota-hold-until)"
check "QUOTA_HOLD_EXPIRED logged"      "1"       "$(grep -ac 'QUOTA_HOLD_EXPIRED' "$(lanelog 1)" || true)"

summary
