#!/usr/bin/env bash
# T9: the recovery path. Needs a cooperating xbabe2, so ssh is stubbed to
# return verification results good enough for a verdict to be ACCEPTED --
# otherwise every sandbox fire downgrades to UNKNOWN and the branch that
# releases a hold on success is never reached.
set -uo pipefail
cd "$(dirname "$0")"; . ./harness.sh

install_good_ssh() {
    cat > "$SB/bin/fakessh" <<'SSHEOF'
#!/usr/bin/env bash
# argv: xbabe2 "<remote command>"   (stdin may be remote_verify.py)
cmd="${2:-}"
case "$cmd" in
  *"python3 - "*)
      cat >/dev/null                      # swallow the piped script
      tok=${cmd##*python3 - }
      mode=$(python3 -c "import base64,json,sys;print(json.loads(base64.b64decode(sys.argv[1])).get('mode',''))" "$tok" 2>/dev/null || echo "")
      case "$mode" in
        snapshot) echo '{"check":"OK","snapshot":{},"ledger_lines":10}' ;;
        verify)   echo '{"check":"OK","verified_new_signed":1,"signing_violations_in_module":0,"ledger_has_fire_id":true,"positive_control":{"ok":true,"reason":""},"directive_citation":{"ok":true,"reason":""},"rejected":[]}' ;;
        donecheck) echo '{"pass":true}' ;;
        *) exit 1 ;;
      esac ;;
  *"cut -d"*)
      # Remote pipelines ending in `cut` yield a bare hash. The directive drift
      # check compares it against the picked item's index (multi-directive), so
      # answer from the sha-map of every registered doc; anything else reads as
      # a superseded directive and blocks that item's verdict.
      hit=$(grep -F "$(echo "$cmd" | grep -oE "docs/directives/[A-Za-z0-9._-]+\.md" | head -1)" \
                 "$(dirname "$0")/../sha-map" 2>/dev/null | awk '{print $2}' | head -1)
      echo "${hit:-1111111111111111111111111111111111111111111111111111111111111111}" ;;
  *sha256sum*) echo "0000000000000000000000000000000000000000000000000000000000000000  /remote/file" ;;
  *"cat >>"*|*mkdir*) cat >/dev/null ;;
  *) cat >/dev/null 2>/dev/null; exit 0 ;;
esac
SSHEOF
    chmod +x "$SB/bin/fakessh"
    # sha-map from EVERY registered index: "md_path sha256" per line
    : > "$SB/sha-map"
    for idx in "$SB"/directives/*.index.json; do
        printf '%s %s\n' "$(jq -r '.directive.md_path' "$idx")" \
                         "$(jq -r '.directive.md_sha256' "$idx")" >> "$SB/sha-map"
    done
    sed -i "s|^SSH=false$|SSH=$SB/bin/fakessh|" "$SB/claude-hourly-loop.sh"
    grep -q "^SSH=$SB/bin/fakessh$" "$SB/claude-hourly-loop.sh" || { echo "stub install failed"; exit 1; }
}

GOOD='RUN_SUMMARY_JSON: {"module":"amphora-rdkit-ffi","outcome":"CLAIM_REFUTED","artifacts":["a/b.dsse.json"],"receipts_added":1,"data_asks_added":0,"notes":"real verdict"}'
DUD='RUN_SUMMARY_JSON:  {"module":"amphora-rdkit-ffi","outcome":"UNKNOWN","artifacts":[],"receipts_added":0,"data_asks_added":0,"notes":"nothing"}'
lastout2() { tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .outcome; }

echo "T9: a verified verdict releases a hold at any backoff level"
sandbox_reset; install_good_ssh

fire 0 "$GOOD"
check "verdict accepted with a cooperating xbabe2" "CLAIM_REFUTED" "$(lastout2)"
check "saturation counter at 0"                    "0"             "$(st consecutive-no-progress.txt)"

# drive the gate to a deep hold, then let a real verdict land on the probe
fire 0 "$DUD"; fire 0 "$DUD"; fire 0 "$DUD"
check "gate tripped"                  "3" "$(st consecutive-no-progress.txt)"
fire 0 "$DUD"
check "holding"                       "SATURATION_SKIP" "$(lastout2)"
echo $(( $(date +%s) - 10 )) > "$SB/state/gate-hold-until"
echo 4 > "$SB/state/gate-hold-level"          # pretend we are deep in backoff
fire 0 "$GOOD"                                 # probe succeeds
check "probe banked a verdict"        "CLAIM_REFUTED" "$(lastout2)"
check "hold-until cleared"            "-"   "$(st gate-hold-until)"
check "hold level cleared"            "-"   "$(st gate-hold-level)"
check "STALLED removed"               "no"  "$([ -f "$SB/state/STALLED" ] && echo yes || echo no)"
check "saturation reset"              "0"   "$(st consecutive-no-progress.txt)"
check "recovered event emitted"       "1"   "$(grep -c '"event":"recovered"' "$SB/logs/heartbeat.jsonl" || true)"

echo
echo "T10: fire_class/agent_rc land on a normal successful fire"
check "fire_class OK"                 "OK"  "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .fire_class)"
check "agent_rc 0"                    "0"   "$(tail -1 "$SB/logs/fire-summary.jsonl" | jq -r .agent_rc)"

echo
echo "T11: MISSED_HOURS is no longer blinded by skip rows"
sandbox_reset; install_good_ssh
# a real fire 3h ago, then nothing but gate skips since
python3 - "$SB/logs/fire-summary.jsonl" <<'PY'
import json,sys,datetime as dt
now=dt.datetime.now(dt.timezone.utc)
rows=[{"ts":(now-dt.timedelta(hours=3)).isoformat(),"outcome":"CLAIM_REFUTED"}]
rows+=[{"ts":(now-dt.timedelta(hours=h)).isoformat(),"outcome":"SATURATION_SKIP"} for h in (2,1)]
open(sys.argv[1],"w").write("".join(json.dumps(r)+"\n" for r in rows))
PY
fire 0 "$GOOD"
check "warns about the 3h gap despite fresh skip rows" "1" \
      "$(grep -ac 'MISSED_HOURS' "$(lanelog 1)" || true)"

summary
