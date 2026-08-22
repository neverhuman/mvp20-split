#!/usr/bin/env python3
"""AUDIT_ONLY: amphora-molecule-design-gate implementation source-hash
binding integrity audit.

Target claim: amphora-molecule-design-gate/docs/mission.md ("Honest current
state") and docs/capability-profile.json (evidence_inventory.implementation)
both assert that the module's "live checked implementation" at
amphora-molecule-capabilities/src/lib.rs has SHA-256
5968f518f199cf697d153018afdfee887e9b3ec0bee8a9c00dcc3c5a854ec861.
capability-profile.json's own automatic_demotion list names "source hash
mutation" as an automatic-demotion trigger, i.e. this hash binding is
itself a claim the module relies on for its own integrity story.

Refutation criterion (declared a priori): the claimed hash does not equal
sha256(current committed content of amphora-molecule-capabilities/src/lib.rs).
Any mismatch is sufficient; deterministic string comparison, no threshold.

Runs entirely off already-committed, already-signed, or plain on-disk
content -- no new data acquired, no dataset touched, no manifest touched.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-molecule-design-gate"
TARGET_FILE_RELPATH = "amphora-molecule-capabilities/src/lib.rs"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(cmd, cwd=ROOT):
    return subprocess.run(cmd, cwd=cwd, shell=True, check=True,
                           capture_output=True, text=True).stdout


def main():
    # 1. Actual current content hash, two independent measurements.
    working_bytes = (ROOT / TARGET_FILE_RELPATH).read_bytes()
    working_sha = sha(working_bytes)

    head_hash = run("git rev-parse HEAD").strip()
    head_blob = run(f"git show HEAD:{TARGET_FILE_RELPATH}")
    head_blob_bytes = head_blob.encode()
    head_sha = sha(head_blob_bytes)

    git_status_line = run(f"git status --short -- {TARGET_FILE_RELPATH}").strip()

    baseline_commit = run(
        f"git log --oneline -- {TARGET_FILE_RELPATH}"
    ).strip().splitlines()[-1].split()[0]
    baseline_blob = run(f"git show {baseline_commit}:{TARGET_FILE_RELPATH}")
    baseline_sha = sha(baseline_blob.encode())

    # 2. Claimed hash, extracted from the module's own machine-readable
    #    capability-profile.json (structured field, not regex).
    cap_profile = json.loads((MODULE / "docs/capability-profile.json").read_text())
    claimed_hash_capability_profile = cap_profile["evidence_inventory"]["implementation"]["sha256"]
    claimed_path_capability_profile = cap_profile["evidence_inventory"]["implementation"]["path"]
    automatic_demotion_triggers = cap_profile.get("automatic_demotion", [])

    # 3. Claimed hash, extracted from mission.md prose (regex over the
    #    documented citation pattern "`amphora-molecule-capabilities/src/lib.rs`
    #    with SHA-256 `<hex>`" and the "Focused checked test evidence" bullet).
    mission_text = (MODULE / "docs/mission.md").read_text()
    mission_hash_hits = re.findall(
        r"amphora-molecule-capabilities/src/lib\.rs`[^`]*SHA-256\s*`([a-f0-9]{64})`",
        mission_text,
    )

    # 4. Independent cross-validation: unrelated audits in DIFFERENT modules
    #    (amphora-candidate-contract, amphora-molecule-generator) recorded
    #    their own source_hashes / actual-hash measurements for the same
    #    physical file path from their own independent runs. If they
    #    disagree with (1) that would be a red flag about MY measurement,
    #    not about mission.md.
    cross_checks = {}
    cc_path_1 = (
        ROOT / "amphora-candidate-contract/evidence/audit/"
        "eight-vector-facts-injection-v1/diagnostic.canonical.json"
    )
    if cc_path_1.exists():
        cc = json.loads(cc_path_1.read_text())
        cross_checks["amphora-candidate-contract/eight-vector-facts-injection-v1"] = (
            cc.get("source_hashes", {}).get(TARGET_FILE_RELPATH)
        )
    cc_path_2 = (
        ROOT / "amphora-molecule-generator/evidence/audit/"
        "molgen-implementation-hash-binding-integrity-v1/"
        "molgen-implementation-hash-binding-integrity-receipt.v1.dsse.json"
    )
    if cc_path_2.exists():
        cc2 = json.loads(cc_path_2.read_text())
        payload_b64 = cc2["signature"]["payload"]
        import base64 as _b64
        payload = json.loads(_b64.standard_b64decode(payload_b64))
        cross_checks["amphora-molecule-generator/molgen-implementation-hash-binding-integrity-v1"] = (
            payload.get("measurements", {}).get("actual_sha256_working_tree")
        )

    # 5. Portfolio-wide grep (structural, not claimed-authoritative beyond
    #    this module) for how many OTHER modules' own mission.md/
    #    capability-profile.json cite the exact same stale hash for the
    #    exact same shared file -- reported as context only, out of scope
    #    to fix (different modules), never modified.
    grep_out = run(
        "grep -rl "
        f"'{claimed_hash_capability_profile}' "
        "--include='*.md' --include='*.json' . "
        "| grep -E '/(docs/mission\\.md|docs/capability-profile\\.json)$' "
        "| sort"
    )
    other_modules_citing_stale_hash = sorted({
        line.split("/docs/")[0].lstrip("./")
        for line in grep_out.splitlines() if line.strip()
    })

    working_matches_head = working_sha == head_sha
    working_matches_baseline = working_sha == baseline_sha
    actual_hash_stable_and_committed = (
        working_matches_head and working_matches_baseline and git_status_line == ""
    )

    mismatch_capability_profile = claimed_hash_capability_profile != working_sha
    mismatch_mission_md = any(h != working_sha for h in mission_hash_hits)
    cross_checks_agree_with_actual = {
        k: (v == working_sha if v else None) for k, v in cross_checks.items()
    }

    verdict = "CLAIM_REFUTED" if (mismatch_capability_profile or mismatch_mission_md) else "CLAIM_SURVIVED"

    result = {
        "study_id": "DESIGNGATE_IMPLEMENTATION_HASH_BINDING_INTEGRITY_V1",
        "target_claim": {
            "claim_text": (
                "mission.md 'Honest current state' and capability-profile.json "
                "evidence_inventory.implementation both assert SHA-256 "
                f"{claimed_hash_capability_profile} for the module's live "
                f"checked implementation at {TARGET_FILE_RELPATH}."
            ),
            "capability_profile_path": "amphora-molecule-design-gate/docs/capability-profile.json",
            "mission_md_path": "amphora-molecule-design-gate/docs/mission.md",
            "automatic_demotion_trigger_invoked": "source hash mutation",
            "automatic_demotion_triggers_declared": automatic_demotion_triggers,
        },
        "refutation_criterion": (
            "claimed_hash != sha256(current git-committed content of "
            f"{TARGET_FILE_RELPATH}); any mismatch refutes, deterministic "
            "string comparison, no tolerance."
        ),
        "measurements": {
            "target_file_relpath": TARGET_FILE_RELPATH,
            "target_file_path_as_declared_in_capability_profile": claimed_path_capability_profile,
            "claimed_hash_capability_profile": claimed_hash_capability_profile,
            "claimed_hash_occurrences_mission_md": mission_hash_hits,
            "actual_sha256_working_tree": working_sha,
            "actual_sha256_git_head_blob": head_sha,
            "actual_sha256_git_baseline_commit_blob": baseline_sha,
            "git_head_commit": head_hash,
            "git_baseline_commit_that_added_file": baseline_commit,
            "git_status_short_for_target_file": git_status_line,
            "working_tree_matches_head_blob": working_matches_head,
            "working_tree_matches_baseline_commit_blob": working_matches_baseline,
            "actual_hash_stable_and_committed_not_live_drift": actual_hash_stable_and_committed,
            "independent_cross_check_sources": list(cross_checks.keys()),
            "independent_cross_check_hashes": cross_checks,
            "independent_cross_checks_agree_with_actual_hash": cross_checks_agree_with_actual,
        },
        "findings": {
            "mismatch_capability_profile_vs_actual": mismatch_capability_profile,
            "mismatch_mission_md_vs_actual": mismatch_mission_md,
            "n_mission_md_hash_citations_checked": len(mission_hash_hits),
            "n_mission_md_hash_citations_mismatched": sum(
                1 for h in mission_hash_hits if h != working_sha
            ),
        },
        "context_other_modules_citing_identical_stale_hash_for_same_shared_file": (
            other_modules_citing_stale_hash
        ),
        "does_not_close": [
            "Does not modify mission.md, capability-profile.json, the manifest, "
            "or any other module's docs -- reports the finding only.",
            "Does not assert amphora-molecule-capabilities/src/lib.rs itself is "
            "functionally broken or that design_gate_result() behaves "
            "differently than documented -- this audit is about the hash "
            "BINDING (provenance claim), not runtime behavior, which prior "
            "T-08 / U-E2E / U-E2E-B live-runtime fires already separately "
            "exercised.",
            "Other modules (amphora-molecule-generator, amphora-molecule-"
            "novelty, amphora-molecule-role-ranker, amphora-molecule-"
            "property) cite the identical stale hash for the identical "
            "shared file; amphora-molecule-generator's own 2026-08-16 fire "
            "already reported and signed this same defect for itself. "
            "Repairing docs in modules other than amphora-molecule-design-"
            "gate is out of scope for this receipt and is reported as "
            "context only.",
            "Does not determine WHY the hash drifted (most likely: the shared "
            "amphora-molecule-capabilities/src/lib.rs crate grew via later "
            "repairs -- e.g. the Wave-R interactive repairs referenced in the "
            "git baseline commit message -- after mission.md's audit_date "
            "2026-07-17 documentation was authored, and the citation was never "
            "recomputed) -- ROOT CAUSE is out of scope; the BINDING FAILURE is "
            "in scope and is what this receipt certifies.",
        ],
        "verdict": verdict,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
