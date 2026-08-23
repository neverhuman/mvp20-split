#!/usr/bin/env bash
# T11: fire-summary appends must stay one-line-per-record under concurrency.
#
# Exists because write_summary.py used Python's buffered writer, which splits
# any payload over 8192 bytes into multiple write() syscalls -- under four
# lanes that is a torn JSONL line, and one torn line silently disables the
# MISSED_HOURS detector (jq -rs slurp fails || true). The rewrite bounds every
# field and issues a single os.write on an O_APPEND fd.
set -uo pipefail
WS="$(cd "$(dirname "$0")/../.." && pwd)/lib/write_summary.py"
OUT=$(mktemp /tmp/amphora-t11.XXXXXX.jsonl)
trap 'rm -f "$OUT"' EXIT
pass=0; fail=0
check() { if [ "$2" = "$3" ]; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1: expected [$2] got [$3]"; fail=$((fail+1)); fi; }

echo "T11: concurrent max-size appends never tear"
BIGREF=$(python3 -c "import json;print(json.dumps({'doc':'X','pad':'y'*3000}))")
PAYLOAD=$(python3 -c "
import json
print(json.dumps({
  'claim_tested':'c'*2000,'attack_type':'a'*2000,'verdict_summary':'v'*2000,
  'notes':'n'*2000,'artifacts':['p'*500]*40,
  'directive_ref':{'doc':'Y','pad':'z'*5000}}))")
for i in $(seq 1 50); do
    printf '%s' "$PAYLOAD" | python3 "$WS" "$OUT" "2026-08-10T00:00:00+00:00" "amphora-x" \
        "CAMPAIGN" "claude-sonnet-5" "ITEM-$i" "pending" "UNKNOWN" "UNKNOWN" "fire-$i" \
        "OK" "OK" "100" "0" "0" "false" "$BIGREF" "0" "OK" "2" &
done
wait
check "50 records written"            "50" "$(wc -l < "$OUT")"
check "every line parses as JSON"     "50" "$(jq -c . "$OUT" 2>/dev/null | wc -l)"
MAXLEN=$(awk '{print length}' "$OUT" | sort -n | tail -1)
check "max line under 8192 (single write)" "yes" "$([ "$MAXLEN" -lt 8192 ] && echo yes || echo no)"
check "oversized directive_ref clipped" "true" "$(head -1 "$OUT" | jq -r '.directive_ref._clipped')"
check "oversized reported ref clipped"  "true" "$(head -1 "$OUT" | jq -r '.directive_ref_reported._clipped')"
check "lane field recorded"             "2"    "$(head -1 "$OUT" | jq -r '.lane')"

echo
echo "T11b: lane defaults to 1 when the launcher predates lanes"
: > "$OUT"
printf '{}' | python3 "$WS" "$OUT" "ts" "m" "MODE" "model" "id" "app" "OK" "OK" "f" "OK" "OK" "1" "0" "0" "false" "" "0" "OK"
check "legacy 19-arg call still writes" "1" "$(wc -l < "$OUT")"
check "lane defaulted"                  "1" "$(head -1 "$OUT" | jq -r '.lane')"

echo; echo "== $pass passed, $fail failed =="; [ "$fail" -eq 0 ]
