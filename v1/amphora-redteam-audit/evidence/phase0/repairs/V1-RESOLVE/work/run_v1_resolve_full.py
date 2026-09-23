#!/usr/bin/env python3
"""V1-RESOLVE full pipeline: run the mechanical sweep, then the read-and-judge
table builder, and emit one combined diagnostic. Two-replay byte-stability is
checked by running this script twice and diffing stdout bytes (done by the
caller); this script itself is pure filesystem read + regex parse + Ed25519
verify against a pinned public key, so it is deterministic given a fixed tree.
"""
import json
import subprocess
import sys

WORK = "/home/ubuntu/amphora/build/mvp20-split/amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work"

sweep = subprocess.run([sys.executable, f"{WORK}/run_v1_resolve_sweep.py"],
                        capture_output=True, check=True)
diag = json.loads(sweep.stdout)

table = subprocess.run([sys.executable, f"{WORK}/build_v1_resolve_table.py", "/dev/stdin"],
                        input=sweep.stdout, capture_output=True, check=True)
table_result = json.loads(table.stdout)

combined = {
    "schema": "amphora.redteam-audit.v1-resolve-retraction-resolution.v1",
    "item_id": "V1-RESOLVE",
    "sweep_summary_counts": diag["summary_counts"],
    "n_index_files": diag["n_index_files"],
    "index_files_found": diag["index_files_found"],
    "n_distinct_superseded_by_targets": diag["n_distinct_superseded_by_targets"],
    "trust_store": diag["trust_store"],
    "resolution_summary": {
        "n_rows": table_result["n_rows"],
        "n_resolved": table_result["n_resolved"],
        "n_not_resolved": table_result["n_not_resolved"],
        "n_not_applicable": table_result["n_not_applicable"],
    },
    "not_resolved_rows": table_result["not_resolved_rows"],
    "resolution_table": table_result["resolution_table"],
}
print(json.dumps(combined, indent=2, sort_keys=True))
