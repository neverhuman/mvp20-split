#!/usr/bin/env bash
# T1/T2: classification + counter isolation, driven by the REAL Aug-6 transcript.
set -uo pipefail
cd "$(dirname "$0")"; . ./harness.sh

QUOTA_MSG="You've hit your weekly limit · resets Aug 7, 12pm (UTC)"
QUOTA_BARE="You've hit your weekly limit · resets 12pm (UTC)"
GOOD='RUN_SUMMARY_JSON: {"module":"amphora-rdkit-ffi","outcome":"CLAIM_REFUTED","artifacts":[],"receipts_added":1,"data_asks_added":0,"notes":"ok"}'

echo "T1: classification"
sandbox_reset
fire 1 "$QUOTA_MSG"
check "quota transcript -> fire_class QUOTA" "QUOTA" "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .fire_class)"
check "quota does NOT bump saturation"       "0"     "$(st consecutive-no-progress.txt)"
check "quota DOES bump infra"                "1"     "$(st consecutive-infra-fail.txt)"
check "quota hold file written"              "yes"   "$([ -s "$SB/state/quota-hold-until" ] && echo yes || echo no)"
check "hold deadline is in the future"       "yes"   "$([ "$(cat "$SB/state/quota-hold-until")" -gt "$(date +%s)" ] && echo yes || echo no)"
check "agent_rc recorded"                    "1"     "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .agent_rc)"

sandbox_reset
fire 124 "agent was killed mid-run"
check "rc=124 -> TIMEOUT"                    "TIMEOUT" "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .fire_class)"
check "timeout does NOT bump saturation"     "0"       "$(st consecutive-no-progress.txt)"

sandbox_reset
fire 1 "ssh: connect to host xbabe2 port 22: No route to host"
check "rc!=0 + no summary -> INFRA"          "INFRA"   "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .fire_class)"

sandbox_reset
fire 0 "$GOOD"
check "clean fire -> OK"                     "OK"      "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .fire_class)"
check "OK fire bumps saturation (no xbabe2 => verdict blocked)" "1" "$(st consecutive-no-progress.txt)"
check "OK fire clears infra"                 "0"       "$(st consecutive-infra-fail.txt)"

echo
echo "T2: no false FATAL on a non-zero agent exit"
sandbox_reset
fire 1 "$QUOTA_MSG"
check "no 'post-processing aborted'"         "0" \
      "$(grep -ac 'post-processing aborted' "$(lanelog 1)" || true)"
check "post-processing still ran (summary row written)" "1" \
      "$(wc -l < "$SB/logs/fire-summary.jsonl")"

echo
echo "T3: bare reset time (no month/day) still parses forward"
sandbox_reset
fire 1 "$QUOTA_BARE"
now=$(date +%s); until=$(cat "$SB/state/quota-hold-until")
check "bare reset is in the future"          "yes" "$([ "$until" -gt "$now" ] && echo yes || echo no)"
check "bare reset within 24h"                "yes" "$([ $((until-now)) -le 86400 ] && echo yes || echo no)"

echo
echo "T4: unparseable limit message falls back to a hold, never to no hold"
sandbox_reset
fire 1 "You've hit your usage limit. Try again later."
until=$(cat "$SB/state/quota-hold-until"); now=$(date +%s)
check "fallback hold applied"                "yes" "$([ "$until" -gt "$now" ] && echo yes || echo no)"
check "fallback is the 6h default"           "yes" "$([ $((until-now)) -gt 21000 ] && [ $((until-now)) -le 21600 ] && echo yes || echo no)"
check "still not counted as saturation"      "0"   "$(st consecutive-no-progress.txt)"

summary
