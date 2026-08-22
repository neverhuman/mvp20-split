#!/usr/bin/env python3
"""AUDIT_ONLY diagnostic assembly for amphora-cro-protocol-packager: adversarial
attack on the CLAIM-LOCK and execution_authority_locked paths of
CroProtocolPackageV2, per campaign item T-02 and founder directive T2-02
(docs/directives/2026-08-05-closing-the-open-portfolio.md, section A.1).

Claim under attack (item T-02): amphora-cro-protocol-packager has never
received an adversarial verdict; its constructive SIGNED_RECEIPT-era
receipts are untested claims.

Method: a real Rust integration test
(amphora-assurance-capabilities/tests/cro_protocol_packager_t02_adversarial_probe.rs)
calling the REAL compiled CroProtocolPackageV2::draft/validate/sign/
verify_signature runtime (amphora-assurance-capabilities/src/lib.rs) -- the
exact production signed-packet code path -- executes:
  (a) execution_authorized -> true
  (b) strip AND null each of the 8 REQUIRED_CRO_CLAIM_LOCKS in turn (16 probes)
  (c) a literal one-byte flip inside the DSSE-signed payload bytes of an
      already-signed packet
  (d) a packet-authored performance/decision threshold
      (locked_numeric_thresholds) paired with a format-valid but
      content-undereived protocol_lock_sha256, with a positive control
      (same construction minus the lock hash) that must be rejected
plus an 8-alternate-encoding injection harness (same taxonomy as the
amphora-candidate-contract T-01 eight-vector-facts-injection probe), run
against BOTH the claim-lock path (claim_locks map) and the
execution_authority_locked path (execution_authorized scalar) -- 16
vector/path combinations. Output was captured twice (two independent test
invocations) and diffed byte-identical before this script ran; both replay
files are embedded verbatim.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-cro-protocol-packager"
OUT_DIR = MODULE / "evidence/audit/t02-claim-lock-execution-authority-adversarial-v1"
HARNESS_RS = OUT_DIR / "harness/cro_protocol_packager_t02_adversarial_probe.rs"
LIB_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
CARGO_TOML = ROOT / "amphora-assurance-capabilities/Cargo.toml"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-05-closing-the-open-portfolio.md"
DIRECTIVE_SHA256_EXPECTED = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --- two-replay gate on the live-runtime probe capture ----------------------
run_a = (OUT_DIR / "probe_output_runA.json").read_bytes()
run_b = (OUT_DIR / "probe_output_runB.json").read_bytes()
assert run_a == run_b, "live-runtime probe not byte-stable across replays"
probe = json.loads(run_a)

assert probe["schema_sanity_draft_ok"] is True
assert probe["n_encoding_vectors"] == 8
assert probe["n_encoding_path_combinations"] == 16

# --- directive pin check -----------------------------------------------------
directive_bytes = DIRECTIVE_MD.read_bytes()
directive_sha256_now = sha(directive_bytes)

# --- source hashes for provenance -------------------------------------------
lib_rs_sha256 = sha(LIB_RS.read_bytes())
cargo_toml_sha256 = sha(CARGO_TOML.read_bytes())
harness_sha256 = sha(HARNESS_RS.read_bytes())

# --- directive (a)-(d) probe table ------------------------------------------
directive_probes = probe["directive_probes"]
directive_slipped = [p for p in directive_probes if not p["fail_closed"]]

# --- 8-encoding x 2-path table ------------------------------------------------
encoding_table = probe["encoding_table"]
encoding_leaks = [row for row in encoding_table if row["leak_detected"]]

n_evaded = probe["n_evaded"]
n_detected_leak = probe["n_detected_leak"]

# --- refutation criterion evaluation (founder's wording, verbatim) ----------
refutation_criterion = (
    "Any mutation verifies, any lock is bypassable, or a packet-authored "
    "threshold is accepted."
)
threshold_probe = next(
    p for p in directive_probes if p["group"] == "directive_d_packet_authored_threshold"
)
refutation_observed = bool(threshold_probe["packet_authored_threshold_accepted"]) or bool(directive_slipped) or bool(encoding_leaks)

headline = (
    f"REFUTED: directive attack (d) -- a packet-authored performance/decision "
    f"threshold in locked_numeric_thresholds, paired with a format-valid but "
    f"content-undereived protocol_lock_sha256 (\"{threshold_probe['protocol_lock_sha256_used'][:16]}...\", "
    f"never the hash of anything), was ACCEPTED end-to-end: validate()=Ok, "
    f"sign()=Ok, verify_signature()=Ok "
    f"(validate_ok={threshold_probe['validate_ok']}, sign_ok={threshold_probe['sign_ok']}, "
    f"verify_signature_ok={threshold_probe['verify_signature_ok']}). protocol_lock_sha256 "
    f"is format-checked (64 lowercase hex) but never content-bound to "
    f"locked_numeric_thresholds anywhere in the codebase -- no producer or "
    f"consumer computes it as a hash of the thresholds it claims to lock. "
    f"A positive control (same construction with protocol_lock_sha256 "
    f"omitted) IS correctly rejected "
    f"(positive_control_missing_lock_hash_rejected="
    f"{threshold_probe['positive_control_missing_lock_hash_rejected']}), proving the "
    f"harness discriminates a real binding defect rather than being vacuously "
    f"green. Separately: directive probes (a) execution_authorized->true, "
    f"(b) strip/null each of the 8 REQUIRED_CRO_CLAIM_LOCKS in turn "
    f"(16 probes), and (c) a one-byte flip inside the DSSE-signed payload of "
    f"an already-signed packet, ALL fail closed "
    f"({len(directive_probes) - 1 - len([p for p in directive_probes if p['group']=='directive_d_packet_authored_threshold'])}"
    f" additional probes beyond (d), 0 slipped through). The 8-alternate-"
    f"encoding injection harness (V1-V8, same taxonomy as the "
    f"amphora-candidate-contract T-01 probe) run against both the claim-lock "
    f"path and the execution_authority_locked path (16 vector/path "
    f"combinations) found 0 leaks -- all 16 EVADED, because "
    f"execution_authorized is a strict top-level scalar field behind "
    f"#[serde(deny_unknown_fields)] (any misnamed/wrapped encoding fails at "
    f"deserialize) and claim_locks required-key membership is checked "
    f"exactly by string equality (any misnamed/homoglyph key fails the "
    f"required-lock presence check at validate()). The encoding harness alone "
    f"would have licensed CLAIM_SURVIVED; the directive (d) threshold-binding "
    f"finding overrides that to CLAIM_REFUTED for the module as a whole, "
    f"because refutation_criterion item (iii) (\"a packet-authored threshold "
    f"is accepted\") DID occur."
)

diagnostic = {
    "schema": "amphora.cro-protocol-packager.t02-adversarial-claim-lock-execution-authority-diagnostic.v1",
    "study_id": "amphora-cro-protocol-packager-t02-claim-lock-execution-authority-adversarial-v1",
    "run_type": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "T-02",
    "directive_ref": {
        "doc": "AMPHORA-DIRECTIVE-2026-08-05",
        "section": "A.1",
        "item_id": "T2-02",
        "owner": "LOOP",
        "md_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
        "md_sha256": DIRECTIVE_SHA256_EXPECTED,
    },
    "directive_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
    "directive_sha256": DIRECTIVE_SHA256_EXPECTED,
    "directive_sha256_verified_now": directive_sha256_now == DIRECTIVE_SHA256_EXPECTED,
    "directive_obligation": "T2-02",
    "axis": (
        "FIRST adversarial test of amphora-cro-protocol-packager (zero prior "
        "ledger verdicts). Targets the CLAIM-LOCK path (claim_locks map, all "
        "8 REQUIRED_CRO_CLAIM_LOCKS) and the execution_authority_locked path "
        "(execution_authorized scalar, ranking_eligible, authority_ceiling) "
        "of the live CroProtocolPackageV2 signed-packet contract, plus the "
        "previously-unexamined locked_numeric_thresholds / "
        "protocol_lock_sha256 binding pair."
    ),
    "claim_under_attack": (
        "amphora-cro-protocol-packager/docs/mission.md (campaign item T-02 "
        "claim_text): amphora-cro-protocol-packager has never received an "
        "adversarial verdict; its constructive SIGNED_RECEIPT-era receipts "
        "(8/8 CRO claim-locks true + sign-verify round-trip 1.0 at n=5, "
        "cro-protocol-packager-signed-packet-kpi.v1.json) are untested "
        "claims about the strength of the packager's claim-lock and "
        "execution-authority enforcement."
    ),
    "refutation_criterion_verbatim": refutation_criterion,
    "refutation_criterion_observed": refutation_observed,
    "refutation_criterion_statement": (
        "REFUTATION DID OCCUR via directive attack (d): a packet-authored "
        "performance/decision threshold (locked_numeric_thresholds) WAS "
        "accepted through validate()/sign()/verify_signature() when paired "
        "with a format-valid but content-undereived protocol_lock_sha256. "
        "This is exactly clause (iii) of the refutation_criterion "
        "(\"a packet-authored threshold is accepted\"). Clauses (i) "
        "(\"any mutation verifies\") and (ii) (\"any lock is bypassable\") "
        "did NOT occur in the remaining 34 probes (19 directive-(a)/(b)/(c) "
        "probes minus the (d) group, plus 16 encoding x path combinations): "
        "execution_authorized=true, all 16 strip/null claim-lock mutations, "
        "and the one-byte signed-payload flip all failed closed, and all 16 "
        "alternate-encoding vector/path combinations were evaded."
    ),
    "founder_directive_done_criteria_verbatim": (
        "Status stays DRAFT_FOR_CRO_FEASIBILITY_REVIEW; every mutation "
        "invalidates the package; every stripped lock fails closed; no "
        "packet-authored threshold is honored."
    ),
    "founder_directive_done_criteria_met": False,
    "founder_directive_done_criteria_met_detail": {
        "status_stays_draft_for_cro_feasibility_review": True,
        "every_mutation_invalidates_the_package": (
            "TRUE for all mutations EXCEPT the (d) threshold-injection "
            "construction, which validates, signs, and verifies "
            "successfully with status still DRAFT_FOR_CRO_FEASIBILITY_REVIEW."
        ),
        "every_stripped_lock_fails_closed": True,
        "no_packet_authored_threshold_is_honored": (
            "FALSE at the validate()/sign()/verify_signature() layer: an "
            "attacker-authored threshold IS accepted into a validly-signed "
            "package (see threshold_injection_probe). This receipt did not "
            "find any downstream consumer that reads locked_numeric_thresholds "
            "to make a decision (see does_not_close) -- 'honored' in the "
            "sense of driving a live decision was not observed because "
            "nothing in the current runtime reads this field for any "
            "purpose. 'Accepted' by the signed-packet contract itself WAS "
            "observed, which is what the refutation_criterion names."
        ),
    },
    "theory_reference": (
        "Saltzer & Schroeder (1975) 'The Protection of Information in "
        "Computer Systems' Proceedings of the IEEE 63(9):1278-1308 -- "
        "complete mediation requires every field that participates in a "
        "trust decision to be independently authenticated, not merely "
        "format-checked; a field that LOOKS like a cryptographic binding "
        "(a 64-hex-char 'lock' hash) but is never computed from the content "
        "it claims to bind provides no actual integrity guarantee. NIST FIPS "
        "180-4 (2015) SHA-256 -- a hash is only a binding if the verifier "
        "recomputes and compares it against the bound content; format "
        "validity (length + alphabet) is not content validity. in-toto "
        "Attestation v1.0 (2020) / DSSE -- the signed envelope faithfully "
        "protects EXACTLY the bytes it signs (this receipt's directive-(c) "
        "one-byte-flip probe confirms that layer holds); it cannot protect "
        "against a field inside those bytes that was never bound to "
        "anything in the first place."
    ),
    "non_circularity": (
        "Uses the REAL compiled amphora-assurance-capabilities crate's "
        "CroProtocolPackageV2::draft/validate/sign/verify_signature (same "
        "public API amphora-cli and the module's own Phase-0 KPI harness "
        "use), invoked from a Rust #[test] integration test in the crate's "
        "own tests/ directory (amphora-assurance-capabilities/tests/"
        "cro_protocol_packager_t02_adversarial_probe.rs), compiled and run "
        "via `cargo test -p amphora-assurance-capabilities --offline`. Not a "
        "Python re-implementation of validate()/sign()/verify_signature()."
    ),
    "harness": "amphora-assurance-capabilities/tests/cro_protocol_packager_t02_adversarial_probe.rs (cargo test, real compiled runtime)",
    "harness_rs_sha256": harness_sha256,
    "probe_stdout_sha256": sha(run_a),
    "two_replay_byte_identical": run_a == run_b,
    "directive_probes": directive_probes,
    "directive_probes_slipped_through": directive_slipped,
    "n_directive_probes": probe["n_directive_probes"],
    "encoding_table": encoding_table,
    "encoding_leaks_detected": encoding_leaks,
    "n_encoding_vectors": probe["n_encoding_vectors"],
    "n_encoding_path_combinations": probe["n_encoding_path_combinations"],
    "n_evaded": n_evaded,
    "n_detected_leak": n_detected_leak,
    "n_slipped_through_total": probe["n_slipped_through_total"],
    "threshold_injection_probe": threshold_probe,
    "source_hashes": {
        "amphora-assurance-capabilities/src/lib.rs": lib_rs_sha256,
        "amphora-assurance-capabilities/Cargo.toml": cargo_toml_sha256,
    },
    "headline": headline,
    "verdict": "REFUTED",
    "does_not_close": [
        "No live production or CLI code path was found that reads "
        "locked_numeric_thresholds or protocol_lock_sha256 for any purpose "
        "(grepped whole workspace: these two fields appear ONLY inside "
        "CroProtocolPackageV2's own definition and its format-only validate() "
        "arm). This receipt does not show a packet-authored threshold being "
        "used to make a live pass/fail decision anywhere today -- it shows "
        "that the signed-packet contract's OWN claim-lock machinery accepts "
        "and signs one, which is what the pre-committed refutation_criterion "
        "names ('a packet-authored threshold is accepted'), independent of "
        "whether a consumer exists yet.",
        "If any future code path is added that reads locked_numeric_thresholds "
        "as an authoritative decision input (e.g. a CRO acceptance gate), "
        "trusting protocol_lock_sha256 as proof the thresholds were host-set "
        "rather than packet-authored, it would be trivially forgeable exactly "
        "as demonstrated here -- this is the live risk this finding flags for "
        "repair, not a hypothetical.",
        "The 8-alternate-encoding sub-harness (V1-V8 x 2 paths) found 0 leaks; "
        "taken alone it would license CLAIM_SURVIVED for the claim-lock and "
        "execution-authority-locked deserialization boundary specifically. "
        "The module-level verdict is REFUTED because of the separate (d) "
        "threshold-binding finding, not because the encoding harness found a "
        "leak.",
        "This probe exercises the Rust runtime only (CroProtocolPackageV2 in "
        "amphora-assurance-capabilities). It does not probe amphora-cli's "
        "invocation surface or any HTTP/CLI boundary that might construct a "
        "packet from untrusted input before calling these APIs.",
    ],
}

canonical_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
out_name = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
(OUT_DIR / out_name).write_bytes(canonical_bytes)

print("n_evaded", n_evaded, "/", probe["n_encoding_path_combinations"])
print("n_detected_leak", n_detected_leak)
print("threshold_injection_accepted", threshold_probe["packet_authored_threshold_accepted"])
print("positive_control_rejected", threshold_probe["positive_control_missing_lock_hash_rejected"])
print("refutation_criterion_observed", refutation_observed)
print("verdict", diagnostic["verdict"])
print("diagnostic_sha256", sha(canonical_bytes))
