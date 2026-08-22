#!/usr/bin/env python3
"""Runs the amphora-tui inspect CLI (record_from() path) against clean +
8 poison vectors (V1 positive control + V2..V8 new encodings), in a fully
isolated scratch CWD per run (.amphora/runs lands under CWD, never touching
shared production state). Extracts CandidateRecord.canonical_structure_hash
and result_hash from final-state.json for each run and reports whether the
injected marker leaked verbatim into the typed field."""
import json
import subprocess
import sys
import hashlib
from pathlib import Path

BINARY = "/home/ubuntu/amphora/build/mvp20-split/target/release/amphora-tui"
FIXTURES = Path("/tmp/cc-vec-sweep-fixtures")
VECTOR_NAMES = [
    "V1_top_level_key", "V2_array_container", "V3_deep_nesting",
    "V4_key_case_variant", "V5_alternate_key_name", "V6_semantic_alt_field",
    "V7_string_container", "V8_unicode_homoglyph_key",
]

MARKER_PREFIX = {
    "V1_top_level_key": "POISON_V1_TOPLEVEL_",
    "V2_array_container": "POISON_V2_ARRAY_",
    "V3_deep_nesting": "POISON_V3_DEEPNEST_",
    "V4_key_case_variant": "POISON_V4_KEYCASE_",
    "V5_alternate_key_name": "POISON_V5_ALTKEY_",
    "V6_semantic_alt_field": "POISON_V6_SEMALT_",
    "V7_string_container": "POISON_V7_STRWRAP_",
    "V8_unicode_homoglyph_key": "POISON_V8_HOMOGLYPH_",
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_one(scratch_root: Path, label: str, candidate_path: Path):
    workdir = scratch_root / label
    workdir.mkdir(parents=True, exist_ok=True)
    cand_copy = workdir / "candidate.json"
    cand_copy.write_bytes(candidate_path.read_bytes())
    proc = subprocess.run(
        [BINARY, "inspect", "--candidate", "candidate.json", "--lane", "molecule", "--headless"],
        cwd=workdir, capture_output=True, text=True, timeout=120,
    )
    runs_dir = workdir / ".amphora" / "runs"
    run_dirs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime)
    assert len(run_dirs) == 1, f"expected exactly one run dir for {label}, got {run_dirs}"
    final_state = json.loads((run_dirs[0] / "final-state.json").read_bytes())
    records = final_state.get("records", [])
    assert len(records) == 1, f"expected exactly one record for {label}"
    record = records[0]
    return {
        "label": label,
        "exit_code": proc.returncode,
        "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
        "candidate_file_sha256": sha(cand_copy.read_bytes()),
        "run_dir_name": run_dirs[0].name,
        "final_state_sha256": sha((run_dirs[0] / "final-state.json").read_bytes()),
        "observed_canonical_structure_hash": record.get("canonical_structure_hash"),
        "observed_result_hash": record.get("result_hash"),
    }


def main():
    scratch_root = Path(sys.argv[1])
    scratch_root.mkdir(parents=True, exist_ok=True)

    clean = run_one(scratch_root, "clean", FIXTURES / "clean_candidate.json")

    per_vector = []
    for name in VECTOR_NAMES:
        obs = run_one(scratch_root, name, FIXTURES / f"{name}.json")
        marker_prefix = MARKER_PREFIX[name]
        observed_hash_field = obs["observed_canonical_structure_hash"]
        leaked = isinstance(observed_hash_field, str) and observed_hash_field.startswith(marker_prefix)
        # V7 leaks the JSON-string-wrapped blob, not a bare marker-prefixed string;
        # detect leak by substring containment for that vector specifically.
        if name == "V7_string_container" and isinstance(observed_hash_field, str):
            leaked = marker_prefix in observed_hash_field
        per_vector.append({
            "vector_id": name,
            "injected_marker_prefix": marker_prefix,
            "candidate_accepted_by_contract_layer": obs["exit_code"] == 0,
            "observed_canonical_structure_hash": observed_hash_field,
            "observed_result_hash_differs_from_clean": obs["observed_result_hash"] != clean["observed_result_hash"],
            "typed_field_leak_detected": leaked,
            "run_detail": obs,
        })

    result = {
        "clean_control": clean,
        "per_vector": per_vector,
        "leaked_vectors": [v["vector_id"] for v in per_vector if v["typed_field_leak_detected"]],
        "non_leaked_vectors": [v["vector_id"] for v in per_vector if not v["typed_field_leak_detected"]],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
