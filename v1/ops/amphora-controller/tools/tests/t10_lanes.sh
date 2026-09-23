#!/usr/bin/env bash
# T10: four-lane concurrency — slots, leases, chain, probe single-spend.
#
# Every scenario here is a failure mode the single-lane launcher provably had
# under concurrency (two picks of the same item, lost campaign updates, a
# fleet HARD_STOP from a sibling's legitimate write, four spent probes): the
# suite runs the REAL launcher several times in parallel against a sandbox.
set -uo pipefail
cd "$(dirname "$0")"; . ./harness.sh

DUD='RUN_SUMMARY_JSON: {"module":"amphora-mod-a","outcome":"UNKNOWN","artifacts":[],"receipts_added":0,"data_asks_added":0,"notes":"nothing"}'
DONE_DUD='RUN_SUMMARY_JSON: {"module":"amphora-mod-a","outcome":"CLAIM_REFUTED","artifacts":[],"receipts_added":1,"data_asks_added":0,"campaign_item_id":"IT-1","campaign_item_status":"done","notes":"claims done"}'

# mini_campaign <n-items> [module-prefix] — n pending items in n distinct modules
mini_campaign() {
    python3 - "$SB/campaign.json" "$1" "${2:-amphora-mod}" <<'PY'
import json, sys
path, n, pfx = sys.argv[1], int(sys.argv[2]), sys.argv[3]
mods = ["%s-%s" % (pfx, chr(ord('a')+i)) for i in range(n)]
items = [{"id": "IT-%d" % (i+1), "module": mods[i], "max_fires": 6,
          "title": "t", "claim": "c", "objective": "o", "done_criterion": "d",
          "done_check": {"kind": "signed_receipt_glob",
                         "glob": "%s/evidence/phase0/repairs/IT-%d/done/**/*.json" % (mods[i], i+1)},
          "status": "pending", "fires": []} for i in range(n)]
json.dump({"_comment": "t10 mini campaign", "items": items,
           "fallback_rotation": {"cursor": 0,
                                 "modules": [{"name": m, "weight": 1} for m in mods]},
           "operator_reserved_paths": []}, open(path, "w"), indent=2)
PY
}
# same_module_campaign <n-items> — n pending items ALL in one module
same_module_campaign() {
    python3 - "$SB/campaign.json" "$1" <<'PY'
import json, sys
path, n = sys.argv[1], int(sys.argv[2])
items = [{"id": "IT-%d" % (i+1), "module": "amphora-mod-a", "max_fires": 6,
          "title": "t", "claim": "c", "objective": "o", "done_criterion": "d",
          "done_check": {"kind": "signed_receipt_glob",
                         "glob": "amphora-mod-a/evidence/phase0/repairs/IT-%d/done/**/*.json" % (i+1)},
          "status": "pending", "fires": []} for i in range(n)]
json.dump({"_comment": "t10", "items": items,
           "fallback_rotation": {"cursor": 0, "modules": [{"name": "amphora-mod-a", "weight": 1}]},
           "operator_reserved_paths": []}, open(path, "w"), indent=2)
PY
}
item_field() { jq -r --arg id "$1" '.items[]|select(.id==$id)|'"$2" "$SB/campaign.json"; }
hist_count() { grep -ac "\"event\": *\"$1\"" "$SB/state/lane-ledger.history.jsonl" 2>/dev/null || true; }

echo "T10a: two concurrent lanes claim DIFFERENT items in DIFFERENT modules; both updates survive"
sandbox_reset; mini_campaign 4
fire_bg 0 "$DUD" 3; sleep 0.4; fire_bg 0 "$DUD" 3; wait
check "two claims recorded"           "2" "$(hist_count claim)"
check "two releases recorded"         "2" "$(hist_count release)"
check "claims are distinct items"     "2" "$(grep -a '"event": "claim"' "$SB/state/lane-ledger.history.jsonl" | jq -r .item_id | sort -u | wc -l)"
check "claims are distinct modules"   "2" "$(grep -a '"event": "claim"' "$SB/state/lane-ledger.history.jsonl" | jq -r .module | sort -u | wc -l)"
check "IT-1 fire record survived"     "1" "$(item_field IT-1 '.fires|length')"
check "IT-2 fire record survived"     "1" "$(item_field IT-2 '.fires|length')"
check "all leases released"           "0" "$(nleases)"
check "summary rows carry two lanes"  "2" "$(jq -r 'select(.lane)|.lane' "$SB/logs/fire-summary.jsonl" | sort -u | wc -l)"

echo
echo "T10b: the cap is structural — 5 simultaneous starts, exactly 4 run"
sandbox_reset; mini_campaign 6
echo 0 > "$SB/agent-rc"; printf '%s\n' "$DUD" > "$SB/agent-out"; echo 4 > "$SB/agent-sleep"
for _ in 1 2 3 4 5; do PATH="$SB/bin:$PATH" bash "$SB/claude-hourly-loop.sh" >/dev/null 2>&1 & done
wait
check "exactly 4 fires started"       "4" "$(alllogs | grep -ac 'START pid' || true)"
check "the 5th logged lanes_full"     "1" "$(grep -ac '"event":"lanes_full"' "$SB/logs/heartbeat.jsonl" || true)"
check "4 distinct lane logs"          "4" "$(ls -d "$SB"/logs/lane-* | wc -l)"
check "4 distinct modules claimed"    "4" "$(grep -a '"event": "claim"' "$SB/state/lane-ledger.history.jsonl" | jq -r .module | sort -u | wc -l)"

echo
echo "T10c: an expired lease (killed lane) is reaped and the module re-claimed"
sandbox_reset; mini_campaign 2
python3 -c "
import json,sys,time
json.dump({'leases':{'amphora-mod-a':{'lane':'9','fire_id':'dead-fire','item_id':'IT-1','ts':'x','expires':int(time.time())-5}}}, open('$SB/state/lane-ledger.json','w'))"
fire 0 "$DUD"
check "expire event recorded"         "1"    "$(hist_count expire)"
check "head item re-claimed"          "IT-1" "$(grep -a '"event": "claim"' "$SB/state/lane-ledger.history.jsonl" | jq -r .item_id | head -1)"

echo
echo "T10d: a LIVE foreign lease hides the module; with no other work the lane declines"
sandbox_reset; same_module_campaign 2
python3 -c "
import json,sys,time
json.dump({'leases':{'amphora-mod-a':{'lane':'9','fire_id':'sibling-fire','item_id':'IT-1','ts':'x','expires':int(time.time())+9999}}}, open('$SB/state/lane-ledger.json','w'))"
fire 0 "$DUD"
check "declined the slot"             "NO_CLAIMABLE_SKIP" "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .outcome)"
check "no fire started"               "0" "$(alllogs | grep -ac 'START pid' || true)"
check "counters unmoved"              "0" "$(st consecutive-no-progress.txt)"
check "foreign lease untouched"       "sibling-fire" "$(jq -r '.leases["amphora-mod-a"].fire_id' "$SB/state/lane-ledger.json")"

echo
echo "T10e: lease stolen mid-fire — record banked, transition suppressed, foreign lease kept"
sandbox_reset; mini_campaign 1
fire_bg 0 "$DONE_DUD" 3
sleep 1   # in-flight: replace the lease as if TTL expired and a sibling claimed
python3 -c "
import json,time
json.dump({'leases':{'amphora-mod-a':{'lane':'2','fire_id':'usurper-fire','item_id':'IT-1','ts':'x','expires':int(time.time())+9999}}}, open('$SB/state/lane-ledger.json','w'))"
wait
check "fire record still banked"      "1" "$(item_field IT-1 '.fires|length')"
check "record flagged lease_lost"     "true" "$(item_field IT-1 '.fires[0].lease_lost // false')"
check "status did NOT flip"           "pending" "$(item_field IT-1 '.status')"
check "done suppressed with reason"   "transition suppressed (lease_lost)" "$(item_field IT-1 '.fires[0].done_rejected // ""')"
check "usurper lease NOT deleted"     "usurper-fire" "$(jq -r '.leases["amphora-mod-a"].fire_id' "$SB/state/lane-ledger.json")"
check "lease_lost event recorded"     "1" "$(hist_count lease_lost)"

echo
echo "T10f: gate probe is single-spend under two simultaneous starts"
sandbox_reset; mini_campaign 4
echo 3 > "$SB/state/consecutive-no-progress.txt"
echo 1 > "$SB/state/gate-hold-level"
echo $(( $(date +%s) - 10 )) > "$SB/state/gate-hold-until"
fire_bg 0 "$DUD" 2; fire_bg 0 "$DUD" 2; wait
check "exactly one probe spent"       "1" "$(alllogs | grep -ac 'GATE_PROBE' || true)"
check "the other lane held"           "1" "$(jq -r 'select(.outcome=="PROBE_WAIT_SKIP")|.outcome' "$SB/logs/fire-summary.jsonl" | wc -l)"
check "level advanced exactly once"   "2" "$(st gate-hold-level)"
check "hold survived the sibling"     "yes" "$([ "$(st gate-hold-until)" != "-" ] && echo yes || echo no)"

echo
echo "T10g: HARD_STOP mid-fire — verdict not banked, no transition, counters untouched"
sandbox_reset; mini_campaign 1
fire_bg 0 "$DONE_DUD" 3
sleep 1; echo "TEST_STOP mid-fire" > "$SB/state/HARD_STOP"
wait
check "outcome forced UNKNOWN"        "UNKNOWN" "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .outcome)"
check "downgrade names HARD_STOP"     "yes" "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .outcome_raw >/dev/null 2>&1 && grep -qa 'HARD_STOP_MIDFIRE' "$(lanelog 1)" && echo yes || echo no)"
check "fire record still banked"      "1" "$(item_field IT-1 '.fires|length')"
check "status did NOT flip"           "pending" "$(item_field IT-1 '.status')"
check "counters untouched"            "0" "$(st consecutive-no-progress.txt)"

echo
echo "T10h: four parallel fruitless fires — counter counts all four, no lost increments"
sandbox_reset; mini_campaign 4
echo 0 > "$SB/agent-rc"; printf '%s\n' "$DUD" > "$SB/agent-out"; echo 2 > "$SB/agent-sleep"
for _ in 1 2 3 4; do PATH="$SB/bin:$PATH" bash "$SB/claude-hourly-loop.sh" >/dev/null 2>&1 & done
wait
check "counter is exactly 4"          "4" "$(st consecutive-no-progress.txt)"

echo
echo "T10i: a transient 429 is one lane's INFRA, never a fleet quota hold"
sandbox_reset; mini_campaign 1
fire 1 "Error: rate limit exceeded, please retry shortly"
check "classified INFRA"              "INFRA" "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .fire_class)"
check "no fleet quota hold"           "-"     "$(st quota-hold-until)"
sandbox_reset; mini_campaign 1
fire 0 "the paper discusses how you might hit your weekly limit in API design"
check "rc=0 + limit-like text stays OK" "OK"  "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .fire_class)"
check "still no quota hold"           "-"     "$(st quota-hold-until)"

echo
echo "T10k: a wedged campaign.lock at claim time declines the slot, mutating nothing"
sandbox_reset; mini_campaign 2
sed -i 's/flock -w 30 221/flock -w 2 221/; s/flock -w 120 221/flock -w 3 221/' "$SB/claude-hourly-loop.sh"
PRE_SHA=$(sha256sum "$SB/campaign.json" | cut -d' ' -f1)
mkdir -p "$SB/state/locks"
( exec 9>"$SB/state/locks/campaign.lock"; flock 9; sleep 8 ) &
HOLDER=$!; sleep 0.5
fire 0 "$DUD"
check "slot declined"                 "CLAIM_LOCK_TIMEOUT_SKIP" "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .outcome)"
check "campaign untouched"            "$PRE_SHA" "$(sha256sum "$SB/campaign.json" | cut -d' ' -f1)"
check "counters unmoved"              "0" "$(st consecutive-no-progress.txt)"
wait "$HOLDER" 2>/dev/null || true

echo
echo "T10l: a wedged campaign.lock at UPDATE time loses the record LOUDLY — and mutates nothing"
sandbox_reset; mini_campaign 2
sed -i 's/flock -w 30 221/flock -w 2 221/; s/flock -w 120 221/flock -w 3 221/' "$SB/claude-hourly-loop.sh"
mkdir -p "$SB/state/locks"
# The fake agent plants the wedge itself: structurally after the claim, before
# the update. No wall-clock races.
echo 10 > "$SB/agent-wedge"
fire 0 "$DUD"
rm -f "$SB/agent-wedge"
check "CAMPAIGN_UPDATE_LOST alerted"  "1" "$(alllogs | grep -ac 'ALERT CAMPAIGN_UPDATE_LOST' || true)"
check "record NOT banked (as alerted)" "0" "$(item_field IT-1 '.fires|length')"
check "lease left for the TTL reap"   "1" "$(nleases)"
check "summary records update-lost"   "update-lost" "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .item_status_applied)"

echo
echo "T10m: an INFRA-classified probe leaves the backoff ladder intact (no false RECOVERED)"
sandbox_reset; mini_campaign 2
echo 3 > "$SB/state/consecutive-no-progress.txt"
echo 2 > "$SB/state/gate-hold-level"
expire_gate2() { echo $(( $(date +%s) - 10 )) > "$SB/state/gate-hold-until"; }
expire_gate2
fire 1 "ssh: connect to host xbabe2 port 22: No route to host"   # probe never ran: INFRA
check "probe spent"                   "1" "$(alllogs | grep -ac 'GATE_PROBE' || true)"
check "counters split sub-threshold"  "2 1" "$(st consecutive-no-progress.txt) $(st consecutive-infra-fail.txt)"
expire_gate2
fire 0 "$DUD"                                                     # hold expired, counters nonzero
check "hold artifacts NOT deleted"    "yes" "$([ -f "$SB/state/gate-hold-level" ] && echo yes || echo no)"
check "no false RECOVERED"            "0" "$(alllogs | grep -ac 'RECOVERED: stall cleared' || true)"

echo
echo "T10j: an out-of-band campaign edit breaks the hash chain and is announced"
sandbox_reset; mini_campaign 3
fire 0 "$DUD"                                   # establishes the chain
python3 -c "
import json
c=json.load(open('$SB/campaign.json')); c['_comment']='edited outside the lock'
json.dump(c, open('$SB/campaign.json','w'), indent=2)"
fire 0 "$DUD"
check "chain_rebase event recorded"   "1" "$(hist_count chain_rebase)"
check "ALERT CAMPAIGN_CHAIN logged"   "1" "$(alllogs | grep -ac 'ALERT CAMPAIGN_CHAIN' || true)"
check "loop continued regardless"     "2" "$(hist_count claim)"

summary
