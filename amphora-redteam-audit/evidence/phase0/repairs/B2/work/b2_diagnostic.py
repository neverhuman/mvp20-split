#!/usr/bin/env python3
"""B2 repair diagnostic: the two-writer schema-era defect on
<module>/evidence/phase0/benchmark/result.v1.json.

Deterministic (no clock, no environment): re-derives, from the tree alone,
(1) both writers of the shipped Phase-0 benchmark result,
(2) the per-module binding between the shipped bytes and the SHA-256 pinned in
    each module's immutable signed Phase-0 evaluation receipt,
(3) the honest per-module Phase-0 phase and its reason.

Usage: b2_diagnostic.py <output.json>
"""
import hashlib
import json
import os
import re
import sys

ROOT = "/home/ubuntu/amphora/build/mvp20-split"


def sha_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def rel(path):
    return os.path.relpath(path, ROOT)


def module_ids():
    manifest = json.load(open(os.path.join(ROOT, "module-manifest.json")))
    return sorted(m["project"] for m in manifest["modules"])


def harness_writers():
    """Every integration test that used to write shipped Phase-0 evidence."""
    rows = []
    pattern = re.compile(
        r"fn result_path\(\) -> PathBuf \{\n(?P<body>.*?)\n\}\n", re.S)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if "/target" in dirpath or "/.git" in dirpath:
            dirnames[:] = []
            continue
        if os.path.basename(dirpath) != "tests":
            continue
        for name in sorted(filenames):
            if not name.endswith("_phase0_kpi.rs"):
                continue
            path = os.path.join(dirpath, name)
            text = open(path).read()
            if "write result artifact" not in text:
                continue
            match = pattern.search(text)
            body = match.group("body") if match else ""
            target = "CARGO_TARGET_TMPDIR" if "CARGO_TARGET_TMPDIR" in body else "SHIPPED_EVIDENCE"
            rows.append({
                "file": rel(path),
                "sha256": sha_file(path),
                "writes_to": target,
            })
    return sorted(rows, key=lambda r: r["file"])


def runtime_writer():
    path = os.path.join(ROOT, "amphora-cli/src/phase0.rs")
    text = open(path).read()
    return {
        "file": rel(path),
        "sha256": sha_file(path),
        "function": "evaluate",
        "write_call": 'write_json_immutable(&result_path, &result)',
        "declares_write_call": 'let result_path = phase0_dir.join("benchmark/result.v1.json");' in text,
        "verifier_functions": [
            "verify_module_with_replay",
            "verify_evaluation_result",
            "verify_deterministic_diagnostic",
            "benchmark_execution_complete",
        ],
    }


def module_rows():
    rows = []
    for module in module_ids():
        base = os.path.join(ROOT, module, "evidence/phase0")
        receipt_path = os.path.join(base, "receipts/evaluation.v1.dsse.json")
        review_path = os.path.join(base, "receipts/independent-review.v1.dsse.json")
        result_path = os.path.join(base, "benchmark/result.v1.json")
        events_dir = os.path.join(ROOT, module, "movement/events")
        events = sorted(f for f in os.listdir(events_dir)) if os.path.isdir(events_dir) else []
        events = [e for e in events if e.endswith(".json")]
        pinned = None
        if os.path.isfile(receipt_path):
            pinned = json.load(open(receipt_path)).get("metrics", {}).get("benchmark_result_sha256")
        on_disk = sha_file(result_path) if os.path.isfile(result_path) else None
        shape = None
        if on_disk:
            doc = json.load(open(result_path))
            first = doc.get("first_replay", {})
            shape = "RUNTIME" if isinstance(first, dict) and "execution_passed" in first else "MODULE_HARNESS"
        rows.append({
            "module_id": module,
            "has_evaluation_receipt": os.path.isfile(receipt_path),
            "has_independent_review": os.path.isfile(review_path),
            "movement_event_count": len(events),
            "shipped_result_present": on_disk is not None,
            "shipped_result_shape": shape,
            "shipped_result_sha256": on_disk,
            "receipt_pinned_result_sha256": pinned,
            "binding_matches": (pinned == on_disk) if pinned else None,
        })
    return rows


def classify(row):
    if not row["has_evaluation_receipt"]:
        return "PRE_PHASE_0", "EVALUATION_SIGNATURE_ABSENT"
    if row["binding_matches"] is False:
        return "PRE_PHASE_0", "EVALUATION_RESULT_MISMATCH_BENCHMARK_BYTES_DESTROYED_BY_HARNESS_WRITER"
    if not row["has_independent_review"]:
        return "PRE_PHASE_0", "INDEPENDENT_REVIEW_SIGNATURE_ABSENT"
    if row["movement_event_count"] != 1:
        return "PRE_PHASE_0", "NO_SINGLE_VALID_MOVEMENT_EVENT"
    return "PHASE_0", "EVALUATED_REVIEWED_AND_MOVED_WITH_INTACT_BENCHMARK_BINDING"


def main(argv):
    rows = module_rows()
    for row in rows:
        phase, reason = classify(row)
        row["derived_phase"] = phase
        row["derived_reason"] = reason
    harness = harness_writers()
    diagnostic = {
        "schema": "amphora.phase0-repair.B2-two-writer-diagnostic.v1",
        "repair_item": "B2",
        "authority": "AUDIT_ONLY",
        "defect": (
            "Two writers produced <module>/evidence/phase0/benchmark/result.v1.json "
            "in incompatible shapes. The runtime evaluator writes the RUNTIME "
            "envelope and pins its exact SHA-256 into the immutable signed Phase-0 "
            "evaluation receipt; the per-module KPI integration harnesses "
            "overwrote the same path with the MODULE-HARNESS report shape, "
            "destroying the evaluated bytes and silently dropping the module out "
            "of phase0_count."
        ),
        "writers": {
            "runtime_authority_writer": runtime_writer(),
            "module_harness_writers": harness,
            "module_harness_writer_count": len(harness),
            "module_harness_writers_still_targeting_shipped_evidence": [
                r["file"] for r in harness if r["writes_to"] != "CARGO_TARGET_TMPDIR"
            ],
        },
        "modules": rows,
        "counts": {
            "modules": len(rows),
            "with_evaluation_receipt": sum(1 for r in rows if r["has_evaluation_receipt"]),
            "binding_intact": sum(1 for r in rows if r["binding_matches"] is True),
            "binding_destroyed": sum(1 for r in rows if r["binding_matches"] is False),
            "runtime_shape_on_disk": sum(1 for r in rows if r["shipped_result_shape"] == "RUNTIME"),
            "module_harness_shape_on_disk": sum(
                1 for r in rows if r["shipped_result_shape"] == "MODULE_HARNESS"),
            "derived_phase0_count": sum(1 for r in rows if r["derived_phase"] == "PHASE_0"),
            "derived_pre_phase0_count": sum(1 for r in rows if r["derived_phase"] != "PHASE_0"),
        },
        "does_not": [
            "does not modify any signed receipt, movement event, benchmark lock, "
            "locked fixture, manifest, or mission front-matter",
            "does not promote, demote, or re-sign any module",
            "does not weaken amphora-cli/src/phase0.rs verification",
        ],
    }
    payload = json.dumps(diagnostic, indent=2, sort_keys=True) + "\n"
    with open(argv[1], "w") as fh:
        fh.write(payload)
    print(argv[1], hashlib.sha256(payload.encode()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
