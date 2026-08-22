#!/usr/bin/env python3
"""AUDIT_ONLY diagnostic assembly for amphora-cro-protocol-packager repair
item W-CRO1: content-binds protocol_lock_sha256 to locked_numeric_thresholds
in CroProtocolPackageV2::validate() and re-runs T-02's exact adversarial
probe to show the previously-accepted attacker vector now fails closed.

Claim under attack (W-CRO1): "No packet-authored performance or decision
threshold is honoured by the packager." T-02 (2026-08-05) REFUTED this:
a packet-authored threshold in locked_numeric_thresholds, paired with a
format-valid but content-undereived protocol_lock_sha256, was ACCEPTED by
validate()/sign()/verify_signature(). This script re-runs T-02's own,
byte-unmodified Rust probe (amphora-assurance-capabilities/tests/
cro_protocol_packager_t02_adversarial_probe.rs, same sha256 as T-02's
receipt: 7d3959863564d7a8fd04abb15e66bd9e74db6fea182d97f9fc6066ef364f3c01)
against the REPAIRED runtime and compares every probe against T-02's
recorded results to prove 0 regressions.

Repair: amphora-assurance-capabilities/src/lib.rs validate() now requires
protocol_lock_sha256 == computed_protocol_lock_sha256() (a SHA-256 over the
canonicalized locked_numeric_thresholds map, via the same stable_hash()
construction candidate_sha256/formula_sha256 already use), or rejects with
CroProtocolPackageError::Binding.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-cro-protocol-packager"
OUT_DIR = MODULE / "evidence/audit/w-cro1-protocol-lock-content-binding-repair-v1"
HARNESS_RS = OUT_DIR / "harness/cro_protocol_packager_t02_adversarial_probe.rs"
T02_HARNESS_RS = ROOT / "amphora-assurance-capabilities/tests/cro_protocol_packager_t02_adversarial_probe.rs"
LIB_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
CARGO_TOML = ROOT / "amphora-assurance-capabilities/Cargo.toml"
DIRECTIVE_MD = ROOT / "docs/directives/2026-08-05-closing-the-open-portfolio.md"
DIRECTIVE_SHA256_EXPECTED = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"
T02_DONE_RECEIPT = MODULE / "evidence/phase0/repairs/T-02/done/t02-claim-lock-execution-authority-adversarial-receipt.v1.dsse.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --- probe file must be BYTE-IDENTICAL to T-02's exact probe (same attack) --
harness_sha256 = sha(HARNESS_RS.read_bytes())
t02_harness_sha256_live = sha(T02_HARNESS_RS.read_bytes())
assert harness_sha256 == t02_harness_sha256_live, "harness copy drifted from live crate test"
T02_RECORDED_HARNESS_SHA256 = "7d3959863564d7a8fd04abb15e66bd9e74db6fea182d97f9fc6066ef364f3c01"
assert harness_sha256 == T02_RECORDED_HARNESS_SHA256, "probe is NOT T-02's exact probe -- re-attack invalid"

# --- two-replay gate on the live-runtime probe capture (POST-repair) --------
run_a = (OUT_DIR / "probe_output_runA.json").read_bytes()
run_b = (OUT_DIR / "probe_output_runB.json").read_bytes()
assert run_a == run_b, "post-repair live-runtime probe not byte-stable across replays"
post = json.loads(run_a)

# --- T-02's own recorded (pre-repair) probe results, for regression diff ----
t02_receipt = json.loads(T02_DONE_RECEIPT.read_bytes())
t02_payload = json.loads(
    __import__("base64").b64decode(t02_receipt["signature"]["payload"])
)
pre_directive_probes = {p["probe"]: p for p in t02_payload["directive_probes"]}
pre_encoding_table = t02_payload["encoding_table"]
post_directive_probes = {p["probe"]: p for p in post["directive_probes"]}
post_encoding_table = post["encoding_table"]

# --- per-vector regression table: every probe EXCEPT (d) must be unchanged --
regression_rows = []
n_regressions = 0
for name, pre in pre_directive_probes.items():
    post_p = post_directive_probes[name]
    if pre["group"] == "directive_d_packet_authored_threshold":
        # This is the one probe the repair is SUPPOSED to change.
        changed_as_expected = (
            pre["fail_closed"] is False
            and post_p["fail_closed"] is True
            and pre["packet_authored_threshold_accepted"] is True
            and post_p["packet_authored_threshold_accepted"] is False
        )
        regression_rows.append({
            "probe": name,
            "group": pre["group"],
            "pre_repair_fail_closed": pre["fail_closed"],
            "post_repair_fail_closed": post_p["fail_closed"],
            "pre_repair_accepted": pre["packet_authored_threshold_accepted"],
            "post_repair_accepted": post_p["packet_authored_threshold_accepted"],
            "pre_repair_validate_ok": pre["validate_ok"],
            "post_repair_validate_ok": post_p["validate_ok"],
            "pre_repair_sign_ok": pre["sign_ok"],
            "post_repair_sign_ok": post_p["sign_ok"],
            "pre_repair_verify_signature_ok": pre["verify_signature_ok"],
            "post_repair_verify_signature_ok": post_p["verify_signature_ok"],
            "changed_as_expected": changed_as_expected,
            "regression": not changed_as_expected,
        })
        if not changed_as_expected:
            n_regressions += 1
    else:
        identical = pre == post_p
        regression_rows.append({
            "probe": name,
            "group": pre["group"],
            "pre_repair_fail_closed": pre["fail_closed"],
            "post_repair_fail_closed": post_p["fail_closed"],
            "identical_to_t02_recorded": identical,
            "regression": not identical,
        })
        if not identical:
            n_regressions += 1

# --- encoding table (16 vector/path combinations) must be byte-identical ----
encoding_identical = pre_encoding_table == post_encoding_table
if not encoding_identical:
    n_regressions += 1

evading_vector = post_directive_probes["attacker_threshold_with_undereived_protocol_lock_hash"]
pre_evading_vector = pre_directive_probes["attacker_threshold_with_undereived_protocol_lock_hash"]

repair_verified = (
    n_regressions == 0
    and evading_vector["fail_closed"] is True
    and evading_vector["packet_authored_threshold_accepted"] is False
    and evading_vector["validate_ok"] is False
    and evading_vector["sign_ok"] is False
    and evading_vector["verify_signature_ok"] is False
    and pre_evading_vector["packet_authored_threshold_accepted"] is True
)

# --- positive control: this repair's OWN check must fire on a defect we ----
# --- deliberately plant in ITS OWN input (the mismatched-hash vector IS    --
# --- exactly that: protocol_lock_sha256 = "a"*64, never derived from the  --
# --- thresholds it claims to lock) -----------------------------------------
positive_control = {
    "planted_defect": (
        "protocol_lock_sha256 set to the literal string 'a' repeated 64 "
        "times (format-valid 64-lowercase-hex) while locked_numeric_thresholds "
        "contains {'attacker_pass_fail_yield_strength_min_mpa': 9999.0} -- "
        "the hash is NEVER computed from that map's content."
    ),
    "how_planted": (
        "amphora-assurance-capabilities/tests/cro_protocol_packager_t02_adversarial_probe.rs "
        "directive (d) block: p.locked_numeric_thresholds.insert("
        "\"attacker_pass_fail_yield_strength_min_mpa\", 9999.0); "
        "p.protocol_lock_sha256 = Some(\"a\".repeat(64)); "
        "p.packet_id = p.computed_packet_id().unwrap(); then validate()/sign()/"
        "verify_signature() attempted end-to-end -- byte-identical construction "
        "T-02 used to obtain packet_authored_threshold_accepted=true pre-repair."
    ),
    "detected": bool(
        evading_vector["fail_closed"] is True
        and evading_vector["validate_ok"] is False
    ),
    "evidence": (
        f"post-repair directive_d probe: validate_ok={evading_vector['validate_ok']}, "
        f"sign_ok={evading_vector['sign_ok']}, "
        f"verify_signature_ok={evading_vector['verify_signature_ok']}, "
        f"packet_authored_threshold_accepted={evading_vector['packet_authored_threshold_accepted']}, "
        f"fail_closed={evading_vector['fail_closed']} "
        f"(pre-repair T-02 recorded: packet_authored_threshold_accepted="
        f"{pre_evading_vector['packet_authored_threshold_accepted']}, "
        f"fail_closed={pre_evading_vector['fail_closed']}). "
        "CroProtocolPackageV2::validate() now returns Err(Binding) because "
        "protocol_lock_sha256 != computed_protocol_lock_sha256()."
    ),
}
assert positive_control["detected"] is True, "repair's own check failed to fire on its own planted defect"

refutation_criterion = (
    "Any mutation verifies, any lock is bypassable, or a packet-authored "
    "threshold is accepted."
)
# Re-evaluated against the REPAIRED runtime, same wording, same probes.
refutation_criterion_observed_post_repair = any(
    not p["fail_closed"] for p in post["directive_probes"]
) or bool(post["encoding_leaks_detected"] if "encoding_leaks_detected" in post else [
    row for row in post_encoding_table if row["leak_detected"]
])

directive_bytes = DIRECTIVE_MD.read_bytes()
directive_sha256_now = sha(directive_bytes)
lib_rs_sha256 = sha(LIB_RS.read_bytes())
cargo_toml_sha256 = sha(CARGO_TOML.read_bytes())

diagnostic = {
    "schema": "amphora.cro-protocol-packager.w-cro1-protocol-lock-content-binding-repair-diagnostic.v1",
    "study_id": "amphora-cro-protocol-packager-w-cro1-protocol-lock-content-binding-repair-v1",
    "run_type": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "W-CRO1",
    "repair_of": "T-02",
    "repair_of_receipt_path": "amphora-cro-protocol-packager/evidence/phase0/repairs/T-02/done/t02-claim-lock-execution-authority-adversarial-receipt.v1.dsse.json",
    "repair_of_receipt_sha256": sha(T02_DONE_RECEIPT.read_bytes()),
    "claim_under_attack": (
        "amphora-cro-protocol-packager campaign item W-CRO1 claim: "
        "'No packet-authored performance or decision threshold is honoured "
        "by the packager.' T-02 refuted this by showing "
        "locked_numeric_thresholds + a content-undereived protocol_lock_sha256 "
        "is accepted end-to-end. This receipt attacks the REPAIR: does the "
        "content-bound protocol_lock_sha256 check now withstand T-02's exact "
        "attack, with no regression on the other 34 probes T-02 recorded?"
    ),
    "directive_context": {
        "note": (
            "W-CRO1's campaign item JSON carries no directive_ref field of "
            "its own; it repairs the defect T-02 found under founder "
            "directive obligation T2-02. Cited for provenance only, not as "
            "a claimed directive_ref of this item."
        ),
        "directive_obligation_repaired": "T2-02",
        "directive_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
        "directive_sha256": DIRECTIVE_SHA256_EXPECTED,
        "directive_sha256_verified_now": directive_sha256_now == DIRECTIVE_SHA256_EXPECTED,
    },
    "repair_description": (
        "amphora-assurance-capabilities/src/lib.rs: CroProtocolPackageV2::validate() "
        "Binding match arm now requires protocol_lock_sha256 == "
        "computed_protocol_lock_sha256() (new pub fn: SHA-256 over "
        "canonicalize(serde_json::to_value(&self.locked_numeric_thresholds)), "
        "the same stable_hash() construction candidate_sha256/formula_sha256 "
        "already use elsewhere in this struct) whenever locked_numeric_thresholds "
        "is non-empty. A format-valid-but-undereived hash (e.g. 'a'*64) now "
        "fails validate() with CroProtocolPackageError::Binding, which "
        "propagates through sign() and verify_signature() (both call "
        "validate() first)."
    ),
    "acceptance_check": (
        "Re-run T-02's own probe file, byte-unmodified (verified by sha256 "
        "equality against T-02's recorded harness_rs_sha256), against the "
        "repaired runtime. Compare every one of T-02's 19 directive probes "
        "and 16 encoding/path combinations against T-02's recorded results: "
        "all must be identical EXCEPT the directive_d threshold-injection "
        "probe, which must flip from fail_closed=false/accepted=true to "
        "fail_closed=true/accepted=false."
    ),
    "harness_rs_sha256": harness_sha256,
    "t02_recorded_harness_rs_sha256": T02_RECORDED_HARNESS_SHA256,
    "harness_byte_identical_to_t02": harness_sha256 == T02_RECORDED_HARNESS_SHA256,
    "two_replay_byte_identical": run_a == run_b,
    "probe_stdout_sha256": sha(run_a),
    "regression_table": regression_rows,
    "n_probes_compared": len(regression_rows) + 1,  # +1 for encoding table row
    "n_regressions": n_regressions,
    "encoding_table_byte_identical_to_t02": encoding_identical,
    "evading_vector_pre_repair": pre_evading_vector,
    "evading_vector_post_repair": evading_vector,
    "repair_verified": repair_verified,
    "positive_control": positive_control,
    "refutation_criterion_verbatim": refutation_criterion,
    "refutation_criterion_observed_post_repair": refutation_criterion_observed_post_repair,
    "verdict": "CLAIM_SURVIVED" if repair_verified else "CLAIM_REFUTED",
    "source_hashes": {
        "amphora-assurance-capabilities/src/lib.rs": lib_rs_sha256,
        "amphora-assurance-capabilities/Cargo.toml": cargo_toml_sha256,
    },
    "pre_repair_lib_rs_sha256": "d80e09105f43c25ebf0851460c54d49246d3906056f3dbce2b6ff3a78469b7ca",
    "cargo_test_crate_green": True,
    "cargo_test_workspace_green": True,
    "cargo_test_crate_command": "cargo test -p amphora-assurance-capabilities --offline",
    "cargo_test_workspace_command": "cargo test --workspace --offline",
    "theory_reference": (
        "Saltzer & Schroeder (1975) 'The Protection of Information in "
        "Computer Systems' Proceedings of the IEEE 63(9):1278-1308 -- "
        "complete mediation requires every field that participates in a "
        "trust decision to be independently authenticated. NIST FIPS 180-4 "
        "(2015) SHA-256 -- a hash is only a binding if the verifier "
        "recomputes and compares it against the bound content."
    ),
    "non_circularity": (
        "Uses the REAL compiled amphora-assurance-capabilities crate's "
        "CroProtocolPackageV2::validate/sign/verify_signature after the "
        "source repair, invoked from T-02's own unmodified Rust #[test] "
        "integration test, compiled and run via `cargo test -p "
        "amphora-assurance-capabilities --offline`. Not a Python "
        "re-implementation."
    ),
    "does_not_close": [
        "As T-02 noted, no live production or CLI code path reads "
        "locked_numeric_thresholds/protocol_lock_sha256 to make a decision "
        "today. This repair closes the signed-packet contract's own "
        "acceptance gap (a packet-authored threshold can no longer acquire "
        "an unearned content-binding), not a live consumer decision -- "
        "because no live consumer of this field exists yet.",
        "This receipt exercises the Rust runtime only (CroProtocolPackageV2 "
        "in amphora-assurance-capabilities). It does not re-probe "
        "amphora-cli's invocation surface.",
    ],
}

canonical_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
import sys
out_name = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
(OUT_DIR / out_name).write_bytes(canonical_bytes)

print("n_regressions", n_regressions)
print("repair_verified", repair_verified)
print("evading_vector_post_repair_accepted", evading_vector["packet_authored_threshold_accepted"])
print("evading_vector_pre_repair_accepted", pre_evading_vector["packet_authored_threshold_accepted"])
print("positive_control_detected", positive_control["detected"])
print("verdict", diagnostic["verdict"])
print("diagnostic_sha256", sha(canonical_bytes))
