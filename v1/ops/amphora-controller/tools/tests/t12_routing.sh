#!/usr/bin/env bash
# T12: multi-directive routing — registry resolution, fail-closed on unknown
# docs, and drift scoped to the picked item's document (one stale directive
# must block ITS items, not freeze the other program's).
set -uo pipefail
cd "$(dirname "$0")"; . ./harness.sh

IDX05="directives/2026-08-05-closing-the-open-portfolio.index.json"
IDX09="directives/2026-08-09-dataset-recon.index.json"

# campaign with ONE item carrying an arbitrary directive_ref
ref_campaign() {  # $1=doc $2=obligation_id $3=md_path $4=md_sha256
    python3 - "$SB/campaign.json" "$@" <<'PY'
import json, sys
path, doc, oid, md, sha = sys.argv[1:6]
ref = {"doc": doc, "section": "S", "item_id": oid, "owner": "LOOP",
       "md_path": md, "md_sha256": sha}
item = {"id": "RT-1", "module": "amphora-mod-a", "max_fires": 6, "title": "t",
        "claim": "c", "objective": "o", "done_criterion": "d",
        "done_check": {"kind": "signed_receipt_glob",
                       "glob": "amphora-mod-a/evidence/phase0/repairs/RT-1/done/**/*.json"},
        "status": "pending", "fires": [], "directive_ref": ref}
json.dump({"_comment": "t12", "items": [item],
           "fallback_rotation": {"cursor": 0, "modules": [{"name": "amphora-mod-a", "weight": 1}]},
           "operator_reserved_paths": []}, open(path, "w"), indent=2)
PY
}

# ssh stub with a path->sha map for sha256sum calls + verify-friendly answers
install_map_ssh() {
    cat > "$SB/bin/fakessh" <<'SSHEOF'
#!/usr/bin/env bash
d="$(dirname "$0")/.."
cmd="${2:-}"
case "$cmd" in
  *"python3 - "*)
      cat >/dev/null
      tok=${cmd##*python3 - }
      mode=$(python3 -c "import base64,json,sys;print(json.loads(base64.b64decode(sys.argv[1])).get('mode',''))" "$tok" 2>/dev/null || echo "")
      case "$mode" in
        snapshot) echo '{"check":"OK","snapshot":{},"ledger_lines":10}' ;;
        verify)   echo '{"check":"OK","verified_new_signed":1,"signing_violations_in_module":0,"ledger_has_fire_id":true,"positive_control":{"ok":true,"reason":""},"directive_citation":{"ok":true,"reason":""},"rejected":[]}' ;;
        donecheck) echo '{"pass":true}' ;;
        *) exit 1 ;;
      esac ;;
  *"cut -d"*)
      hit=$(grep -F "$(echo "$cmd" | grep -oE "docs/directives/[a-z0-9.-]+\.md")" "$d/sha-map" 2>/dev/null | awk '{print $2}' | head -1)
      echo "${hit:-1111111111111111111111111111111111111111111111111111111111111111}" ;;
  *sha256sum*) echo "0000000000000000000000000000000000000000000000000000000000000000  /remote/file" ;;
  *"cat >>"*|*mkdir*) cat >/dev/null ;;
  *) cat >/dev/null 2>/dev/null; exit 0 ;;
esac
SSHEOF
    chmod +x "$SB/bin/fakessh"
    sed -i "s|^SSH=false$|SSH=$SB/bin/fakessh|" "$SB/claude-hourly-loop.sh"
}

GOOD='RUN_SUMMARY_JSON: {"module":"amphora-mod-a","outcome":"CLAIM_REFUTED","artifacts":["a/b.dsse.json"],"receipts_added":1,"data_asks_added":0,"notes":"ok"}'
lastq() { tail -1 "$SB/logs/fire-summary.jsonl" | jq -r "$1"; }

echo "T12a: an item citing an UNKNOWN doc fails closed"
sandbox_reset; install_map_ssh
ref_campaign "AMPHORA-DIRECTIVE-9999-01-01" "GHOST-1" "docs/directives/ghost.md" "aaaa"
fire 0 "$GOOD"
check "verdict downgraded"            "UNKNOWN"       "$(lastq .outcome)"
check "raw verdict preserved"         "CLAIM_REFUTED" "$(lastq .outcome_raw)"
check "UNREGISTERED logged"           "1" "$(grep -ac 'DIRECTIVE_UNREGISTERED' "$(lanelog 1)" || true)"

echo
echo "T12b: routing resolves the 2026-08-09 index and its criterion"
sandbox_reset; install_map_ssh
SHA09=$(jq -r '.directive.md_sha256' "$SB/$IDX09"); MD09=$(jq -r '.directive.md_path' "$SB/$IDX09")
printf '%s %s\n' "$MD09" "$SHA09" > "$SB/sha-map"
ref_campaign "AMPHORA-DIRECTIVE-2026-08-09" "DR-RUBRIC" "$MD09" "$SHA09"
fire 0 "$GOOD"
check "verdict accepted"              "CLAIM_REFUTED" "$(lastq .outcome)"
check "no drift complaint"            "0" "$(grep -ac 'DIRECTIVE_DRIFT' "$(lanelog 1)" || true)"
check "banner shows directive OK"     "1" "$(grep -ac 'directive: OK' "$(lanelog 1)" || true)"

echo
echo "T12c: drift in doc A blocks A's items — and does NOT touch doc B's"
sandbox_reset; install_map_ssh
SHA05=$(jq -r '.directive.md_sha256' "$SB/$IDX05"); MD05=$(jq -r '.directive.md_path' "$SB/$IDX05")
SHA09=$(jq -r '.directive.md_sha256' "$SB/$IDX09"); MD09=$(jq -r '.directive.md_path' "$SB/$IDX09")
# live 05 doc "altered" (stub returns a different sha); live 09 doc correct
printf '%s %s\n%s %s\n' "$MD05" "2222222222222222222222222222222222222222222222222222222222222222" "$MD09" "$SHA09" > "$SB/sha-map"
ref_campaign "AMPHORA-DIRECTIVE-2026-08-05" "T2-04" "$MD05" "$SHA05"
fire 0 "$GOOD"
check "doc-A item blocked on drift"   "UNKNOWN" "$(lastq .outcome)"
check "MISMATCH names the doc"        "1" "$(grep -ac 'DIRECTIVE_DRIFT\[AMPHORA-DIRECTIVE-2026-08-05\]' "$(lanelog 1)" || true)"
ref_campaign "AMPHORA-DIRECTIVE-2026-08-09" "DR-RUBRIC" "$MD09" "$SHA09"
fire 0 "$GOOD"
check "doc-B item still accepted"     "CLAIM_REFUTED" "$(lastq .outcome)"

echo
echo "T12d: an item with NO directive_ref carries no drift constraint"
sandbox_reset; install_map_ssh
: > "$SB/sha-map"           # every remote doc hash would mismatch — must not matter
python3 - "$SB/campaign.json" <<'PY'
import json, sys
item = {"id": "RT-2", "module": "amphora-mod-a", "max_fires": 6, "title": "t",
        "claim": "c", "objective": "o", "done_criterion": "d",
        "done_check": {"kind": "signed_receipt_glob",
                       "glob": "amphora-mod-a/evidence/phase0/repairs/RT-2/done/**/*.json"},
        "status": "pending", "fires": []}
json.dump({"_comment": "t12", "items": [item],
           "fallback_rotation": {"cursor": 0, "modules": [{"name": "amphora-mod-a", "weight": 1}]},
           "operator_reserved_paths": []}, open(sys.argv[1], "w"), indent=2)
PY
fire 0 "$GOOD"
check "accepted with no directive"    "CLAIM_REFUTED" "$(lastq .outcome)"
check "banner shows directive NONE"   "1" "$(grep -ac 'directive: NONE' "$(lanelog 1)" || true)"

echo
echo "T12e: campaign_invariants keys by (doc, item_id) and fails a HUMAN-pending in directive 2"
sandbox_reset
SHA09=$(jq -r '.directive.md_sha256' "$SB/$IDX09"); MD09=$(jq -r '.directive.md_path' "$SB/$IDX09")
python3 - "$SB/campaign.json" "$MD09" "$SHA09" <<'PY'
import json, sys
path, md, sha = sys.argv[1:4]
item = {"id": "DR-RIGHTS", "module": "amphora-dataset-recon", "max_fires": 1, "title": "t",
        "claim": "c", "objective": "o", "done_criterion": "d",
        "done_check": {"kind": "signed_receipt_glob",
                       "glob": "amphora-dataset-recon/evidence/phase0/repairs/DR-RIGHTS/done/**/*.json"},
        "status": "pending", "fires": [],
        "directive_ref": {"doc": "AMPHORA-DIRECTIVE-2026-08-09", "section": "S5",
                          "item_id": "DR-RIGHTS", "owner": "HUMAN",
                          "md_path": md, "md_sha256": sha}}
json.dump({"_comment": "t12", "items": [item],
           "fallback_rotation": {"cursor": 0, "modules": [{"name": "amphora-dataset-recon", "weight": 1}]},
           "operator_reserved_paths": []}, open(path, "w"), indent=2)
PY
# (sandbox_reset already placed REGISTRY.json + both indexes in $SB/directives;
# the invariants tool finds the sibling registry beside the campaign)
RC=0; OUT=$(python3 ../campaign_invariants.py "$SB/campaign.json" 2>&1) || RC=$?
check "invariants exit nonzero"       "1"   "$RC"
check "owner violation named"         "yes" "$(grep -q 'owner=HUMAN but status=pending' <<<"$OUT" && echo yes || echo no)"

summary
