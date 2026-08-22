#!/usr/bin/env python3
"""DSSE-Ed25519-sign the kpi-claim-currency-v1 receipt for
amphora-formulation-universe. AUDIT_ONLY. Does NOT promote authority, does
NOT flip scientific_readiness, does NOT modify the manifest, KPI,
benchmark-lock, live Rust engine, or mission.md.
"""
import base64
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-formulation-universe"
ITEM = MOD / "evidence/audit/kpi-claim-currency-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260815T110001-1563621-999baa0fa684"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (ITEM / "diagnostic.canonical.json").read_bytes()
runB = (ITEM / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

harness_sha = sha((ITEM / "run_kpi_claim_currency.py").read_bytes())
t06_receipt_sha = sha((MOD / "evidence/phase0/repairs/T-06/done/t06-independent-adversarial-attack-receipt.v1.dsse.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.formulation-universe.kpi-claim-currency-receipt.v1",
    "study_id": "kpi-claim-currency-v1",
    "module": "amphora-formulation-universe",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "verdict": "CLAIM_REFUTED",
    "claim_under_attack": {
        "receipt_path": "amphora-formulation-universe/evidence/phase0/kpis/"
            "formulation-universe-cartesian-accounting-kpi.v1.json",
        "claim_text": "The machine-readable Phase-0 KPI register (metric "
            "'cartesian_canonical_duplication_fail_closed_rate', observed=1.0, "
            "passed=true, probe_sample_size=4, note='CARTESIAN_CANONICAL_DUPLICATION "
            "attack axis. Four probes: literal string duplicate, integer duplicate, "
            "null duplicate, canonically-equal objects with different JSON key "
            "insertion orders (defeated via amphora_core::stable_hash). All return "
            "Err.') is a CURRENT, non-stale, accurate characterization of the "
            "CARTESIAN_CANONICAL_DUPLICATION attack axis -- this is the standing "
            "signed claim the portfolio still relies on, because unlike "
            "docs/mission.md (which was updated with a 'Known contradictions' entry "
            "after T-06), the KPI JSON itself has never been edited, corrected, "
            "retracted, or superseded, and is the one artifact any downstream machine "
            "consumer (not a human reading prose) would actually parse.",
        "distinguishing_note": "This attacks a DIFFERENT target than T-06 "
            "(2026-08-06, CLAIM_REFUTED, signed at "
            "evidence/phase0/repairs/T-06/done/t06-independent-adversarial-attack-"
            "receipt.v1.dsse.json). T-06 red-teamed the live Rust "
            "validate_formulation_universe primitive directly and found the "
            "duplicate-factor-collapse and index-identity-instability defects; that "
            "verdict already stands refuted and is not re-litigated here. This fire "
            "attacks the GOVERNANCE CLAIM that the signed KPI register was kept "
            "current after T-06's refutation -- i.e. whether the correction "
            "discipline this portfolio otherwise requires (RETRACTION-INDEX.md, "
            "supersedes blocks, as used by amphora-formulation-arithmetic's "
            "X-COV-CPVC repair the same day this KPI has sat untouched) was actually "
            "applied to this artifact. It was not.",
    },
    "attack_description": (
        "Four-part audit executed 2026-08-15 (9 days after T-06 signed "
        "2026-08-06): (1) provenance-continuity check -- independently re-hashed "
        "amphora-formulation-capabilities/src/lib.rs and T-06's own red-team test "
        "file (tests/formulation_universe_redteam_t06_independent.rs) and compared "
        "against the sha256 values T-06's own signed receipt recorded as its "
        "test-time provenance, confirming byte-for-byte zero edits to either file "
        "since T-06 fired (no fix has landed); (2) fresh, independent, back-to-back "
        "re-execution TODAY (twice) of T-06's own test file against the live, "
        "unmodified validate_formulation_universe via `cargo test --workspace "
        "--locked -p amphora-formulation-capabilities --test "
        "formulation_universe_redteam_t06_independent -- --nocapture`, parsing the "
        "captured stdout/stderr for the T06_ATTACK2_BRANCH and T06_FINDING "
        "diagnostic lines; (3) a supersession/retraction grep across evidence/ for "
        "any reference to the KPI file path, and an existence check for "
        "evidence/phase0/kpis/RETRACTION-INDEX.md; (4) a git-log check on the KPI "
        "file itself, showing its last commit (2026-08-03, baseline commit "
        "907e753) predates T-06 (2026-08-06) by three days and has never been "
        "touched since."
    ),
    "directive_ref": None,
    "refutation_criterion_verbatim": (
        "The KPI's cartesian_canonical_duplication_fail_closed_rate note, quoted "
        "verbatim, characterizes the CARTESIAN_CANONICAL_DUPLICATION attack axis as "
        "fully covered by its 4 named probes with observed=1.0/passed=true and no "
        "caveat. If a confirmed, independently-reproduced counter-example within "
        "that same attack axis (a duplicate value the axis-level detector fails to "
        "catch) exists, is still live in the exact file the KPI was measured "
        "against, and is not reflected by any retraction/supersession record "
        "against the KPI artifact itself, the KPI register is a stale, incomplete "
        "standing claim."
    ),
    "refutation_criterion_observation_occurred": True,
    "observed_result": {
        "attack2_numeric_type_duplicate_defect_live_today": diag["attack2_numeric_type_duplicate_defect_live_today"],
        "attack3_index_identity_instability_defect_live_today": diag["attack3_index_identity_instability_defect_live_today"],
        "any_named_t06_defect_live_today": diag["any_named_t06_defect_live_today"],
        "kpi_dup_metric_is_currently_stale_and_incomplete": diag["kpi_dup_metric_is_currently_stale_and_incomplete"],
        "parsed_run1": diag["fresh_execution_2026_08_15"]["parsed_run1"],
        "detail": (
            "Fresh re-execution today confirms, byte-for-byte against T-06's own "
            "test file and unmodified lib.rs, that BOTH named T-06 defects remain "
            "live: (a) validate_formulation_universe(axes={'dose_ratio': [1, 1.0]}) "
            "still returns Ok(axis_cardinalities['dose_ratio']=2, cartesian_total=2) "
            "instead of Err -- a single physical dosing value expressed as JSON int "
            "`1` vs float `1.0` inside one axis is not detected as a canonical "
            "duplicate, exactly the class of case the KPI's own 'integer duplicate' "
            "probe implies is covered but is not; (b) two accounting-equivalent "
            "(byte-identical-receipt) universes differing only in one axis's array "
            "order still decode the same declared index (1) to two different "
            "physical formulations (('IPDA','DGEBF') vs ('TETA','DGEBF')). The KPI's "
            "cartesian_canonical_duplication_fail_closed_rate metric presents "
            "observed=1.0/passed=true for this attack axis with no caveat, "
            "hedge, or reference to the T-06 finding anywhere in the KPI JSON "
            "itself, 9 days after that finding was independently confirmed and "
            "signed."
        ),
    },
    "provenance_continuity": diag["provenance_continuity"],
    "governance_gap": {
        "retraction_index_exists": diag["retraction_index_exists"],
        "supersession_or_retraction_references_to_kpi_file": diag["supersession_or_retraction_references_to_kpi_file"],
        "n_supersession_or_retraction_references": diag["n_supersession_or_retraction_references"],
        "mission_md_was_updated_after_t06": True,
        "kpi_json_was_updated_after_t06": False,
        "finding": (
            "mission.md prose was corrected after T-06 (a 'Known contradictions' "
            "entry dated 2026-08-06 now documents the duplicate-factor-collapse and "
            "index-identity-instability defects), but the machine-readable KPI "
            "register -- the artifact a script, not a human, would actually consume "
            "-- was never touched: git log shows its last commit (2026-08-03) "
            "predates T-06 by three days. No evidence/phase0/kpis/RETRACTION-"
            "INDEX.md exists for this module (unlike amphora-formulation-arithmetic, "
            "which added one for its X-COV-CPVC repair the same day), and no file "
            "anywhere under evidence/ references the KPI path in a supersession or "
            "retraction context. A consumer reading only the KPI JSON (skipping "
            "mission.md prose) would still see observed=1.0/passed=true for an "
            "attack axis that has been signed-refuted for 9 days."
        ),
    },
    "scope_and_limits": {
        "tested_artifact": "the live, unmodified Rust runtime "
            "(amphora-formulation-capabilities::validate_formulation_universe) via "
            "T-06's own independent test file, and the formulation-universe-"
            "cartesian-accounting-kpi.v1.json KPI register only.",
        "no_promotion": True, "no_manifest_edit": True, "no_kpi_edit": True,
        "no_mission_md_edit": True, "no_scientific_readiness_flip": True,
        "no_live_rust_engine_edit": True,
        "remediation_needed": "Human/future-fire action: either correct the KPI's "
            "cartesian_canonical_duplication_fail_closed_rate note to disclose the "
            "numeric-type-evasion gap via a proper supersession with a "
            "RETRACTION-INDEX.md entry, or fix the underlying stable_hash() "
            "canonicalization defect (normalize numeric type/representation before "
            "hashing) and re-derive the KPI from a passing re-run. Neither requires "
            "manifest/human ceremony since this KPI is AUDIT_ONLY / "
            "scientific_readiness NOT_APPLICABLE.",
    },
    "provenance": {
        "harness_path": "amphora-formulation-universe/evidence/audit/"
            "kpi-claim-currency-v1/run_kpi_claim_currency.py",
        "harness_sha256": harness_sha,
        "lib_rs_under_test_path": "amphora-formulation-capabilities/src/lib.rs",
        "lib_rs_under_test_sha256": diag["provenance_continuity"]["lib_rs_sha256_now"],
        "t06_test_file_path": "amphora-formulation-capabilities/tests/"
            "formulation_universe_redteam_t06_independent.rs",
        "t06_test_file_sha256": diag["provenance_continuity"]["t06_test_file_sha256_now"],
        "kpi_examined_path": "amphora-formulation-universe/evidence/phase0/kpis/"
            "formulation-universe-cartesian-accounting-kpi.v1.json",
        "kpi_examined_sha256": diag["provenance_continuity"]["kpi_sha256_now"],
        "t06_receipt_path": "amphora-formulation-universe/evidence/phase0/repairs/"
            "T-06/done/t06-independent-adversarial-attack-receipt.v1.dsse.json",
        "t06_receipt_sha256": t06_receipt_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent full re-run of run_kpi_claim_currency.py "
            "(deterministic parsing of two live cargo test invocations already "
            "captured to run1.out.txt/run1.err.txt and run2.out.txt/run2.err.txt; "
            "no randomness, no wall-clock reads besides the fixed run_date literal)",
        "seed": "n/a -- deterministic, no stochastic seed",
        "cargo_test_command": diag["fresh_execution_2026_08_15"]["command"],
        "cargo_stdout_two_replay_byte_identical": diag["fresh_execution_2026_08_15"]["run1_run2_stdout_byte_identical"],
        "cargo_stderr_note": diag["fresh_execution_2026_08_15"]["stderr_nondeterminism_note"],
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY ad-hoc audit receipt under "
            "evidence/audit/kpi-claim-currency-v1/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.formulation-universe-kpi-claim-currency+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payloadType": ptype, "payload": base64.standard_b64encode(body).decode(),
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

out = ITEM / "kpi-claim-currency-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("kpi_dup_metric_is_currently_stale_and_incomplete", diag["kpi_dup_metric_is_currently_stale_and_incomplete"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
