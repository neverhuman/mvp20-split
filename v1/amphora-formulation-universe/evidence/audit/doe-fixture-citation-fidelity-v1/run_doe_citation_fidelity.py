#!/usr/bin/env python3
"""Harness for doe-fixture-citation-fidelity-v1 (AUDIT_ONLY).

Parses the two independently captured cargo test replays of
`formulation_universe_doe_citation_fidelity_v1.rs` and emits a
deterministic diagnostic JSON (timing-noise stripped) for each replay, so
the two can be compared byte-for-byte.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-universe"
ITEM = MOD / "evidence/audit/doe-fixture-citation-fidelity-v1"
CAP = ROOT / "amphora-formulation-capabilities"

FIRE_ID = "20260817T050001-3280050-bf83a9be45cd"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def parse_run(out_path, err_path):
    out = out_path.read_text()
    err = err_path.read_text()

    m_result = re.search(
        r"test result: (\w+)\. (\d+) passed; (\d+) failed; (\d+) ignored", out
    )
    assert m_result, f"no test-result summary line in {out_path}"

    m_mismatches = re.search(r"DOE_CITATION_FIDELITY_MISMATCHES=(\[.*\])", err)
    assert m_mismatches, f"no DOE_CITATION_FIDELITY_MISMATCHES line in {err_path}"
    mismatches = json.loads(m_mismatches.group(1))

    m_examined = re.search(
        r"DOE_CITATION_FIDELITY_FRACTIONAL_ENTRIES_EXAMINED=(\d+)", err
    )
    assert m_examined, f"no fractional-entries-examined line in {err_path}"

    test_names = sorted(re.findall(r"^test (\S+) \.\.\. (ok|FAILED)$", out, re.M))

    return {
        "test_result_status": m_result.group(1),
        "passed": int(m_result.group(2)),
        "failed": int(m_result.group(3)),
        "ignored": int(m_result.group(4)),
        "individual_tests": test_names,
        "doe_citation_fidelity_mismatches": mismatches,
        "fractional_entries_examined": int(m_examined.group(1)),
    }


def build_diagnostic(out_path, err_path):
    parsed = parse_run(out_path, err_path)
    return {
        "schema": "amphora.formulation-universe.doe-citation-fidelity-diagnostic.v1",
        "study_id": "doe-fixture-citation-fidelity-v1",
        "module": "amphora-formulation-universe",
        "fire_id": FIRE_ID,
        "command": (
            "cargo test --workspace --locked -p amphora-formulation-capabilities "
            "--test formulation_universe_doe_citation_fidelity_v1 -- --nocapture"
        ),
        "fixture_examined": {
            "path": "amphora-formulation-universe/reference/"
            "phase0-formulation-universe-known-answer.v1.json",
            "sha256": sha(
                (
                    MOD
                    / "reference/phase0-formulation-universe-known-answer.v1.json"
                ).read_bytes()
            ),
        },
        "lib_rs_under_test_sha256": sha((CAP / "src/lib.rs").read_bytes()),
        "test_file_sha256": sha(
            (
                CAP
                / "tests/formulation_universe_doe_citation_fidelity_v1.rs"
            ).read_bytes()
        ),
        "mission_md_sha256_at_test_time": sha((MOD / "docs/mission.md").read_bytes()),
        "kpi_json_sha256_at_test_time": sha(
            (
                MOD
                / "evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json"
            ).read_bytes()
        ),
        "parsed": parsed,
    }


def main():
    canonical = build_diagnostic(ITEM / "run1.out.txt", ITEM / "run1.err.txt")
    run_b = build_diagnostic(ITEM / "run2.out.txt", ITEM / "run2.err.txt")

    # Two independently captured cargo test invocations (run1.*.txt,
    # run2.*.txt) must parse to byte-identical diagnostics -- timing/build
    # noise lives only in the raw captured files, never in the parsed
    # diagnostic, matching the kpi-claim-currency-v1 precedent.
    assert canonical == run_b, "replay parsed diagnostics differ"

    (ITEM / "diagnostic.canonical.json").write_text(
        json.dumps(canonical, indent=2, sort_keys=True)
    )
    (ITEM / "diagnostic.runB.json").write_text(
        json.dumps(run_b, indent=2, sort_keys=True)
    )
    print("two_replay_parsed_fields_match", True)
    print(
        "mismatches_found",
        len(canonical["parsed"]["doe_citation_fidelity_mismatches"]),
    )
    print(
        "fractional_entries_examined",
        canonical["parsed"]["fractional_entries_examined"],
    )


if __name__ == "__main__":
    main()
