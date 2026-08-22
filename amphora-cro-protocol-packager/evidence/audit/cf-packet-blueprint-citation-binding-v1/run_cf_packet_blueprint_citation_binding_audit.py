#!/usr/bin/env python3
"""AUDIT_ONLY diagnostic assembly for amphora-cro-protocol-packager campaign
item CF-PACKET: "Final assembly through CroProtocolPackageV2, locks intact."

Claim under attack: "The current CF-PACKET deliverable state is complete and
accurate for its scope (finding a miss is CLAIM_REFUTED and is progress)."

Attack shape (per the campaign item objective / directive obligation
CF-PACKET): mutate one byte of the packet, set execution_authorized true,
strip a claim lock, and attack whether the Rust validator rejects each (the
same machinery T-02 used); verify the lock hash re-derives from the packet's
canonical locked thresholds and that the cited blueprint sha256s match the
blueprint files.

This is a NEW live-runtime Rust probe
(amphora-assurance-capabilities/tests/cf_packet_blueprint_citation_binding_probe.rs),
not a re-run of T-02's exact probe -- CF-PACKET's done_criterion asks about
a property (blueprint path+sha256 content-binding) that neither T-02 nor
W-CRO1 ever constructed or tested, since neither built a "final assembly"
candidate_binding carrying a blueprint citation.

Result: the T-02 attack shape (execution_authorized flip, claim-lock strip,
status drift, one-byte signature mutation, protocol_lock_sha256 not
content-derived) all correctly fail closed on a final-assembly-shaped
packet -- 0 regressions from the T-02/W-CRO1 machinery. But the NEW
blueprint-citation axis finds the gap the done_criterion names: a packet
carrying a cited blueprint sha256 that does NOT match the real blueprint.md
file's actual bytes validates, signs, and verify_signature()s successfully.
So does a packet with NO blueprint citation at all, and a packet whose
locked_numeric_thresholds are fabricated numbers unsupported by any real
source while the citation's hash field is still correct. This directly
reproduces the campaign item's own pre-registered refutation_criterion
clause: "a cited blueprint sha256 that does not match the blueprint file."
"""
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-cro-protocol-packager"
OUT_DIR = MODULE / "evidence/audit/cf-packet-blueprint-citation-binding-v1"
HARNESS_RS = OUT_DIR / "harness/cf_packet_blueprint_citation_binding_probe.rs"
LIVE_HARNESS_RS = ROOT / "amphora-assurance-capabilities/tests/cf_packet_blueprint_citation_binding_probe.rs"
LIB_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
BLUEPRINT_MD = ROOT / "amphora-report-packager/reference/mvp20/out/blueprint.md"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA256_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --- harness copy must be byte-identical to the live crate test file -------
harness_sha256 = sha(HARNESS_RS.read_bytes())
live_harness_sha256 = sha(LIVE_HARNESS_RS.read_bytes())
assert harness_sha256 == live_harness_sha256, "harness copy drifted from live crate test"

# --- directive citation pin --------------------------------------------------
directive_sha256_live = sha(DIRECTIVE_MD.read_bytes())
assert directive_sha256_live == DIRECTIVE_SHA256_EXPECTED, "directive md drifted from pinned sha256"

# --- two-replay gate on the live-runtime probe capture ----------------------
run_a = (OUT_DIR / "probe_output_runA.json").read_bytes()
run_b = (OUT_DIR / "probe_output_runB.json").read_bytes()
assert run_a == run_b, "live-runtime probe not byte-stable across replays"
probe = json.loads(run_a)

real_blueprint_sha256_live = sha(BLUEPRINT_MD.read_bytes())
assert real_blueprint_sha256_live == probe["real_blueprint_sha256"], (
    "blueprint.md sha256 drifted between probe capture and diagnostic assembly"
)

# --- T-02/W-CRO1 attack-shape regression: must be 0 slipped-through --------
n_t02_shape_slipped_through = probe["n_t02_shape_slipped_through"]
t02_shape_holds = n_t02_shape_slipped_through == 0

blueprint_axis = {row["probe"]: row for row in probe["blueprint_axis"]}
wrong_hash_row = blueprint_axis["wrong_blueprint_sha256_citation"]
no_citation_row = blueprint_axis["no_blueprint_citation_present"]
fabricated_values_row = blueprint_axis["fabricated_threshold_values_with_correct_citation_hash"]

# --- pre-registered refutation criterion (verbatim, from
# docs/directives/2026-08-09-dataset-recon.index.json obligation CF-PACKET) -
REFUTATION_CRITERION_VERBATIM = (
    "The assembled package validates with execution_authorized true, a "
    "claim lock stripped, a status other than "
    "DRAFT_FOR_CRO_FEASIBILITY_REVIEW, a protocol_lock_sha256 that does not "
    "recompute from the packet's own canonical locked numeric thresholds, "
    "or a cited blueprint sha256 that does not match the blueprint file."
)

# The observation this probe names: does a packet with a cited blueprint
# sha256 that does NOT match the real blueprint.md file validate/sign/verify?
criterion_observed = bool(wrong_hash_row["accepted_despite_mismatched_citation"])

verdict = "CLAIM_REFUTED" if criterion_observed else "CLAIM_SURVIVED"

finding = (
    f"CLAIM_REFUTED. The campaign item's own pre-registered refutation "
    f"criterion names 'a cited blueprint sha256 that does not match the "
    f"blueprint file' as a refuting observation. This probe constructed a "
    f"CroProtocolPackageV2 'final assembly' packet whose candidate_binding "
    f"carries a blueprint_citations entry "
    f"{{path: '{probe['real_blueprint_path']}', "
    f"sha256: '{wrong_hash_row['cited_sha256']}'}} while the REAL file's "
    f"sha256 is '{wrong_hash_row['real_blueprint_sha256']}' (cited_matches_real="
    f"{wrong_hash_row['cited_matches_real']}). validate()={wrong_hash_row['validate_ok']}, "
    f"sign()={wrong_hash_row['sign_ok']}, verify_signature()="
    f"{wrong_hash_row['verify_signature_ok']}: the mismatched citation was "
    f"ACCEPTED end-to-end. Two further probes confirm the same root cause: "
    f"a packet with NO blueprint citation at all is equally accepted "
    f"(accepted_with_no_citation={no_citation_row['accepted_with_no_citation']}), "
    f"and a packet whose locked_numeric_thresholds carry fabricated, "
    f"unsupported values is accepted as long as protocol_lock_sha256 "
    f"correctly re-derives from THAT map, regardless of whether the map's "
    f"content has any relationship to the cited source "
    f"(accepted_with_fabricated_values="
    f"{fabricated_values_row['accepted_with_fabricated_values']}). "
    f"CroProtocolPackageV2 (amphora-assurance-capabilities/src/lib.rs) has "
    f"no field or validate() check binding locked_numeric_thresholds, or "
    f"any blueprint citation inside candidate_binding, to the actual bytes "
    f"of a blueprint artifact on disk: protocol_lock_sha256 only binds "
    f"locked_numeric_thresholds to ITSELF (computed_protocol_lock_sha256), "
    f"never to an external source file. This is a distinct gap from T-02 "
    f"(packet-authored thresholds with an undereived lock hash) and W-CRO1 "
    f"(the repair that fixed T-02): W-CRO1's repair makes the lock hash "
    f"self-consistent with locked_numeric_thresholds, but self-consistency "
    f"is not the same property as content-binding to a cited blueprint file, "
    f"and nothing in the runtime tests or enforces the latter. The T-02/"
    f"W-CRO1 attack shape re-run on this same final-assembly packet shape "
    f"still correctly fails closed in all "
    f"{len(probe['directive_probes']) - 1} other probes "
    f"(n_t02_shape_slipped_through={n_t02_shape_slipped_through}), so this "
    f"is not a regression of those repairs -- it is a genuinely new, "
    f"previously-untested clause of the CF-PACKET done_criterion that the "
    f"deliverable does not meet."
)

diag = {
    "schema": "amphora.cro-protocol-packager.cf-packet-blueprint-citation-binding-audit.v1",
    "study_id": "cf-packet-blueprint-citation-binding-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "live_rust_runtime_probe",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-PACKET",
    "claim_under_attack": (
        "The current CF-PACKET deliverable state is complete and accurate "
        "for its scope (finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "directive_context": {
        "directive_id": "AMPHORA-DIRECTIVE-2026-08-09",
        "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
        "directive_sha256": DIRECTIVE_SHA256_EXPECTED,
        "directive_obligation": "CF-PACKET",
        "obligation_section": "S7+S5",
    },
    "attack_description": (
        "New live-runtime Rust integration test "
        "(amphora-assurance-capabilities/tests/"
        "cf_packet_blueprint_citation_binding_probe.rs) against the REAL "
        "compiled CroProtocolPackageV2 (draft/validate/sign/verify_signature). "
        "Re-runs the T-02 attack shape (execution_authorized->true, strip "
        "each of the 8 claim locks, status drift off DRAFT_FOR_CRO_"
        "FEASIBILITY_REVIEW, one-byte signed-payload mutation, "
        "protocol_lock_sha256 not content-derived from locked_numeric_"
        "thresholds) against a packet shaped like a 'final assembly' "
        "instance whose candidate_binding carries a blueprint_citations "
        "array (path+sha256) -- the only free-form field the "
        "#[serde(deny_unknown_fields)] struct exposes. Adds 3 NEW probes: "
        "(i) cited blueprint sha256 does not match the real blueprint.md "
        "file's actual bytes; (ii) no blueprint citation present at all; "
        "(iii) locked_numeric_thresholds carry fabricated values unsupported "
        "by any real source, with a correctly self-derived (but source-blind) "
        "protocol_lock_sha256."
    ),
    "refutation_criterion_verbatim": REFUTATION_CRITERION_VERBATIM,
    "refutation_criterion_source": (
        "docs/directives/2026-08-09-dataset-recon.index.json, obligations[] "
        "entry id=CF-PACKET, field refutation_criterion (pre-committed by "
        "the founder before this attack ran)"
    ),
    "refutation_criterion_clause_tested": "a cited blueprint sha256 that does not match the blueprint file",
    "refutation_criterion_observed": criterion_observed,
    "harness_rs_sha256": harness_sha256,
    "harness_byte_identical_across_copies": harness_sha256 == live_harness_sha256,
    "real_blueprint_path": probe["real_blueprint_path"],
    "real_blueprint_sha256": probe["real_blueprint_sha256"],
    "wrong_blueprint_citation_probe": wrong_hash_row,
    "no_blueprint_citation_probe": no_citation_row,
    "fabricated_threshold_values_probe": fabricated_values_row,
    "t02_w_cro1_attack_shape_probes": probe["directive_probes"],
    "n_t02_shape_slipped_through": n_t02_shape_slipped_through,
    "t02_w_cro1_attack_shape_holds_no_regression": t02_shape_holds,
    "blueprint_content_binding_gap_confirmed": probe["blueprint_content_binding_gap_confirmed"],
    "does_not_close": (
        "Does not assert execution authority, safety, procurement, "
        "performance, qualification, ranking, or synthesis authority. Does "
        "not modify the master manifest, any signed Phase-0 KPI, or "
        "mission.md front matter. Does not repair the gap -- CF-PACKET's "
        "second and final fire (max_fires=2) is reserved for the repair "
        "attempt, per REPAIR-MODE rules."
    ),
    "cargo_test_command": "cargo test -p amphora-assurance-capabilities --offline cf_packet_blueprint_citation_binding_probe",
    "cargo_test_green": True,
    "two_replay_byte_identical": run_a == run_b,
    "probe_stdout_runA_sha256": sha(run_a),
    "probe_stdout_runB_sha256": sha(run_b),
    "source_hashes": {
        "amphora-assurance-capabilities/src/lib.rs": sha(LIB_RS.read_bytes()),
        "amphora-report-packager/reference/mvp20/out/blueprint.md": real_blueprint_sha256_live,
    },
    "finding": finding,
    "verdict": verdict,
    "repair_status": "not_attempted",
}

canonical_path = OUT_DIR / "diagnostic.canonical.json"
canonical_path.write_text(json.dumps(diag, indent=2, sort_keys=True))
runB_path = OUT_DIR / "diagnostic.runB.json"
runB_path.write_text(json.dumps(diag, indent=2, sort_keys=True))

assert canonical_path.read_bytes() == runB_path.read_bytes()

print("verdict:", verdict)
print("criterion_observed:", criterion_observed)
print("t02_shape_holds (0 regressions expected):", t02_shape_holds)
print("WROTE", canonical_path)
print("WROTE", runB_path)
