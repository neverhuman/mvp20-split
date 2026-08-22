#!/usr/bin/env bash
# 01_pull_data.sh — SSH-pull every input the portfolio-status-2026-08-03 build needs.
# Runs on xbabe1. All source-of-truth data lives on xbabe2 and is read-only from here.
set -euo pipefail

ROOT=/home/ubuntu/amphora/reports/portfolio-status-2026-08-03
DATA=$ROOT/data
mkdir -p "$DATA"

MVP=/home/ubuntu/amphora/build/mvp20-split

echo "[$(date -Iseconds)] pulling module list …"
ssh xbabe2 "ls -d $MVP/amphora-* | xargs -n1 basename | sort" > "$DATA/modules.txt"
N=$(wc -l < "$DATA/modules.txt")
echo "  found $N amphora-* modules"

echo "[$(date -Iseconds)] pulling module-manifest.json …"
scp -q xbabe2:$MVP/module-manifest.json "$DATA/module-manifest.json"

echo "[$(date -Iseconds)] pulling master portfolio scientific-receipts manifest …"
scp -q xbabe2:$MVP/amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json "$DATA/manifest.json"
MANIFEST_SHA=$(sha256sum "$DATA/manifest.json" | awk '{print $1}')
echo "  manifest sha256: $MANIFEST_SHA"
echo "$MANIFEST_SHA" > "$DATA/manifest.sha256"

echo "[$(date -Iseconds)] pulling mission.md front-matter for every module …"
ssh xbabe2 "cd $MVP && for d in amphora-*; do
    if [ -f \"\$d/docs/mission.md\" ]; then
        FM=\$(head -c 8000 \"\$d/docs/mission.md\" | python3 -c \"
import sys, json, re
t = sys.stdin.read()
m = re.match(r'^---\n(\{.*?\})\n---\n', t, re.DOTALL)
if m:
    try:
        print(json.dumps(json.loads(m.group(1))))
    except Exception:
        print('{}')
else:
    print('{}')
\" 2>/dev/null)
        printf '%s\t%s\n' \"\$d\" \"\$FM\"
    else
        printf '%s\t{}\n' \"\$d\"
    fi
done" > "$DATA/frontmatter.tsv"

python3 -c "
import json, sys
out = {}
for line in open('$DATA/frontmatter.tsv'):
    parts = line.rstrip('\n').split('\t', 1)
    if len(parts) == 2:
        try:
            out[parts[0]] = json.loads(parts[1])
        except Exception:
            out[parts[0]] = {}
json.dump(out, open('$DATA/frontmatter.json', 'w'), indent=2, sort_keys=True)
print(f'  frontmatter.json: {len(out)} modules')
"

echo "[$(date -Iseconds)] pulling KPI files (evidence/phase0/kpis/*.json) …"
ssh xbabe2 "find $MVP -path '*/evidence/phase0/kpis/*.json' -type f 2>/dev/null | sort" > "$DATA/kpi_paths.txt"
K=$(wc -l < "$DATA/kpi_paths.txt")
echo "  found $K KPI files"

# Batch-jq the KPI files: one JSON blob per file, joined into a list.
ssh xbabe2 "for f in \$(cat <<'EOF'
$(cat $DATA/kpi_paths.txt)
EOF
); do
    jq -c --arg path \"\$f\" '{
        path: \$path,
        module_id, capability, kpi_id,
        observed_kpi_summary,
        metrics,
        theory,
        n_deterministic_gates_defined, n_deterministic_gates_passed,
        phase0_deterministic_gates_passed,
        scientific_receipt_sha256, scientific_receipt_path,
        authority_ceiling,
        sig_type: (.signature | type),
        sig_valid: ((.signature|type) == \"object\" and (.signature.payloadType != null) and ((.signature.signatures|type) == \"array\") and ((.signature.signatures|length) > 0))
    }' \"\$f\" 2>/dev/null
done" > "$DATA/kpi_lines.jsonl"

python3 -c "
import json
from collections import defaultdict
by_module = defaultdict(list)
for line in open('$DATA/kpi_lines.jsonl'):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    mod = d.get('module_id') or d.get('path','').split('/mvp20-split/')[-1].split('/')[0]
    by_module[mod].append(d)
json.dump(dict(by_module), open('$DATA/kpi_by_module.json', 'w'), indent=2, sort_keys=True)
print(f'  kpi_by_module.json: {len(by_module)} modules, {sum(len(v) for v in by_module.values())} KPIs')
"

echo "[$(date -Iseconds)] pulling scientific receipts (reference/mvp20/data/*.json filtered by schema~=receipt) …"
# All discovery + filtering happens on xbabe2 so the paths never need to leave the host.
ssh xbabe2 "find $MVP -path '*/reference/mvp20/data/*.json' -type f 2>/dev/null | sort | while read f; do
    schema=\$(jq -r '.schema // \"\"' \"\$f\" 2>/dev/null)
    if echo \"\$schema\" | grep -qi 'receipt'; then
        sha=\$(sha256sum \"\$f\" | awk '{print \$1}')
        sig=\$(jq -r '.signature | type' \"\$f\" 2>/dev/null)
        rid=\$(jq -r '.receipt_id // \"\"' \"\$f\" 2>/dev/null)
        payloadType=\$(jq -r '.signature.payloadType // \"\"' \"\$f\" 2>/dev/null)
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \"\$f\" \"\$schema\" \"\$sha\" \"\$sig\" \"\$rid\" \"\$payloadType\"
    fi
done" > "$DATA/receipts.tsv"

python3 -c "
import json
from collections import defaultdict
by_module = defaultdict(list)
for line in open('$DATA/receipts.tsv'):
    parts = line.rstrip('\n').split('\t')
    if len(parts) < 6:
        continue
    path, schema, sha, sig, rid, ptype = parts
    mod = path.split('/mvp20-split/')[-1].split('/')[0]
    by_module[mod].append({
        'path': path,
        'schema': schema,
        'sha256': sha,
        'signature_type': sig,
        'is_signed': sig == 'object' and ptype != '',
        'receipt_id': rid,
        'payload_type': ptype,
    })
json.dump(dict(by_module), open('$DATA/receipts_by_module.json', 'w'), indent=2, sort_keys=True)
print(f'  receipts_by_module.json: {len(by_module)} modules, {sum(len(v) for v in by_module.values())} scientific receipts')
"

echo "[$(date -Iseconds)] copying xbabe1-local cron state …"
cp -f /home/ubuntu/amphora-cron/logs/fire-summary.jsonl "$DATA/fire_summary.jsonl" 2>/dev/null || echo "[]" > "$DATA/fire_summary.jsonl"
cp -f /home/ubuntu/amphora-cron/module-queue.json "$DATA/module_queue.json" 2>/dev/null || echo "{}" > "$DATA/module_queue.json"
cp -f /home/ubuntu/amphora-cron/data-acquisition-queue.jsonl "$DATA/data_asks.jsonl" 2>/dev/null || : > "$DATA/data_asks.jsonl"

echo "[$(date -Iseconds)] pulling README summaries (first paragraph of each module README) …"
ssh xbabe2 "cd $MVP && for d in amphora-*; do
    if [ -f \"\$d/README.md\" ]; then
        first=\$(awk '/^[A-Za-z]/ {print; exit}' \"\$d/README.md\" 2>/dev/null | head -c 400)
        printf '%s\t%s\n' \"\$d\" \"\$first\"
    fi
done" > "$DATA/readme.tsv" || true

python3 -c "
import json
out = {}
for line in open('$DATA/readme.tsv'):
    parts = line.rstrip('\n').split('\t', 1)
    if len(parts) == 2:
        out[parts[0]] = parts[1]
json.dump(out, open('$DATA/readme_summary.json', 'w'), indent=2, sort_keys=True)
print(f'  readme_summary.json: {len(out)} modules')
"

echo "[$(date -Iseconds)] snapshot summary:"
python3 -c "
import json
fm = json.load(open('$DATA/frontmatter.json'))
kpi = json.load(open('$DATA/kpi_by_module.json'))
rec = json.load(open('$DATA/receipts_by_module.json'))
mani = json.load(open('$DATA/manifest.json'))
from collections import Counter
phases = Counter()
readi = Counter()
for m, f in fm.items():
    phases[f.get('phase','NONE')] += 1
    readi[f.get('scientific_readiness','NONE')] += 1
print(f'  phases: {dict(phases)}')
print(f'  readiness: {dict(readi)}')
print(f'  KPIs total: {sum(len(v) for v in kpi.values())} across {len(kpi)} modules')
print(f'  Scientific receipts: {sum(len(v) for v in rec.values())} across {len(rec)} modules')
mk = mani.get('kpis', {})
print(f'  Master manifest: {mk.get(\"n_receipts_indexed\", \"?\")} indexed receipts across {mk.get(\"n_amphora_modules_covered\",\"?\")} modules')
"
echo "[$(date -Iseconds)] done."
