#!/usr/bin/env python3
"""DSSE-Ed25519-sign the kpi-claim-currency-v1 receipt for
amphora-envelope-gates. AUDIT_ONLY. Does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the manifest, KPI, benchmark-lock, or
mission.md.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
ITEM = MOD / "evidence/audit/kpi-claim-currency-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260815T080001-4134654-db447ba98b57"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

canon = (ITEM / "diagnostic.canonical.json").read_bytes()
runB = (ITEM / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

harness_sha = sha((ITEM / "kpi_currency_probe.py").read_bytes())
t03_receipt_sha = sha((MOD / "evidence/phase0/repairs/T-03/done/t03-adversarial-attack-receipt.v1.dsse.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))

body_obj = {
    "schema": "amphora.envelope-gates.kpi-claim-currency-receipt.v1",
    "study_id": "kpi-claim-currency-v1",
    "module": "amphora-envelope-gates",
    "authority": "AUDIT_ONLY",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "verdict": "CLAIM_REFUTED",
    "claim_under_attack": {
        "receipt_path": "amphora-envelope-gates/evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json",
        "claim_text": "The machine-readable Phase-0 KPI register (metric "
            "'envelope_bound_inversion_fail_closed_rate', observed=1.0, passed=true, "
            "note='ENVELOPE_BOUND_INVERSION axis. Three probes: lower > upper, lower = "
            "NaN, upper = Infinity. All return Err.') is a CURRENT, non-stale, accurate "
            "summary of the fail-closed behavior of the oracle it describes -- this is "
            "the standing signed claim the portfolio still relies on, because unlike "
            "docs/mission.md (which was updated after T-03), the KPI JSON itself has "
            "never been edited, corrected, retracted, or superseded, and is the one "
            "artifact any downstream machine consumer (not a human reading prose) would "
            "actually parse.",
        "distinguishing_note": "This attacks a DIFFERENT target than the prior T-03 "
            "(2026-08-05, CLAIM_REFUTED) and W-D-ENVGATE (2026-08-13 x2, CLAIM_REFUTED) "
            "fires against this module. Those attacked the oracle's behavior and the KAT "
            "fixture's sourcing, respectively, and both already stand refuted. This fire "
            "attacks the GOVERNANCE CLAIM that the signed KPI register was kept current "
            "after T-03's refutation -- i.e. whether the correction discipline this "
            "portfolio otherwise requires (RETRACTION-INDEX.md, supersedes blocks) was "
            "actually applied to this artifact. It was not.",
    },
    "attack_description": (
        "Two-part audit executed 2026-08-15 (10 days after T-03 signed 2026-08-05): "
        "(1) provenance-continuity check -- independently re-hashed the oracle file "
        "(benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py) and the KPI "
        "file (evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json) and "
        "compared against the sha256 values T-03's own signed receipt recorded as its "
        "test-time provenance, confirming byte-for-byte zero edits to either file since "
        "before T-03 fired; (2) fresh re-execution TODAY of the exact 3 named sub-probes "
        "the KPI's own note claims ('lower > upper, lower = NaN, upper = Infinity. All "
        "return Err.') against the real, unmodified, imported evaluate_gate(), using the "
        "actual registered dgeba-teta-primer-9to1 policy and a full nominal 3-feature "
        "snapshot (not a synthetic strawman); (3) a supersession/retraction grep across "
        "evidence/ for any reference to the KPI file path, and an existence check for "
        "evidence/phase0/kpis/RETRACTION-INDEX.md."
    ),
    "directive_ref": None,
    "refutation_criterion_verbatim": (
        "The KPI's envelope_bound_inversion_fail_closed_rate note, quoted verbatim, "
        "asserts all 3 of its named sub-probes (lower>upper, lower=NaN, upper=Infinity) "
        "currently return Err (REJECT). If fresh execution of those exact 3 sub-probes "
        "against the live, unmodified oracle shows fewer than 3/3 returning REJECT, and "
        "no retraction/supersession record exists for the KPI, the KPI is a stale, false "
        "standing claim."
    ),
    "refutation_criterion_observation_occurred": True,
    "observed_result": {
        "n_probes": diag["n_probes"],
        "n_fired_as_expected": diag["n_fired_as_expected"],
        "observed_rate_today": diag["observed_rate_today"],
        "per_probe": diag["fresh_probe_results_2026_08_15"],
        "kpi_note_is_currently_true": diag["kpi_note_is_currently_true"],
        "kpi_metric_is_currently_stale_and_false": diag["kpi_metric_is_currently_stale_and_false"],
        "detail": (
            "Only 1/3 sub-probes (lower_gt_upper) fires as the KPI note claims. "
            "lower_is_nan returns verdict=FAIL with binding_margin=NaN (a non-abstaining "
            "NaN scalar on an invalid bound, not REJECT). upper_is_infinity returns "
            "verdict=PASS with binding_margin=1.0 (a non-abstaining, value-bearing PASS "
            "on an unbounded/invalid policy, not REJECT) -- i.e. a real, registered TETA "
            "policy with its upper bound corrupted to +Infinity still PASSES today, "
            "exactly the value-free-bypass class T-03 already proved and that remains "
            "live and unpatched 10 days later."
        ),
    },
    "provenance_continuity": diag["provenance_continuity"],
    "governance_gap": {
        "retraction_index_exists": diag["retraction_index_exists"],
        "supersession_or_retraction_references_to_kpi_file": diag["supersession_or_retraction_references_to_kpi_file"],
        "n_supersession_or_retraction_references": diag["n_supersession_or_retraction_references"],
        "mission_md_was_updated_after_t03": True,
        "kpi_json_was_updated_after_t03": False,
        "finding": (
            "mission.md prose was corrected after T-03 (two 'Known contradictions' "
            "entries dated 2026-08-05 and 2026-08-13 now document the oracle and KAT "
            "sourcing defects), but the machine-readable KPI register -- the artifact a "
            "script, not a human, would actually consume -- was never touched. No "
            "RETRACTION-INDEX.md exists in evidence/phase0/kpis/, and no file anywhere "
            "under evidence/ references the KPI path in a supersession or retraction "
            "context. A consumer reading only the KPI JSON (skipping mission.md prose) "
            "would still see observed=1.0/passed=true for a fail-closed metric that has "
            "been signed-refuted for 10 days."
        ),
    },
    "scope_and_limits": {
        "tested_artifact": "the CPython AUDIT_ONLY oracle (evaluate_gate()) and the "
            "envelope-gates-constraint-envelope-kpi.v1.json KPI register only -- NOT the "
            "shipped Rust runtime (amphora-formulation-capabilities), which this fire "
            "does not test.",
        "no_promotion": True, "no_manifest_edit": True, "no_kpi_edit": True,
        "no_mission_md_edit": True, "no_scientific_readiness_flip": True,
        "remediation_needed": "Human/future-fire action: either correct the KPI's "
            "envelope_bound_inversion_fail_closed_rate (and "
            "trusted_feature_substitution_fail_closed_rate, which T-03 also refuted) via "
            "a proper supersession with a RETRACTION-INDEX.md entry, or fix the "
            "underlying oracle defect (math.isfinite() checks on bounds and values) and "
            "re-derive the KPI from a passing re-run. Neither requires manifest/human "
            "ceremony since this KPI is AUDIT_ONLY / NOT_APPLICABLE readiness.",
    },
    "provenance": {
        "harness_path": "amphora-envelope-gates/evidence/audit/kpi-claim-currency-v1/kpi_currency_probe.py",
        "harness_sha256": harness_sha,
        "oracle_under_test_path": "amphora-envelope-gates/benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py",
        "oracle_under_test_sha256": diag["provenance_continuity"]["oracle_sha256_now"],
        "kpi_examined_path": "amphora-envelope-gates/evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json",
        "kpi_examined_sha256": diag["provenance_continuity"]["kpi_sha256_now"],
        "t03_receipt_path": "amphora-envelope-gates/evidence/phase0/repairs/T-03/done/t03-adversarial-attack-receipt.v1.dsse.json",
        "t03_receipt_sha256": t03_receipt_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": "independent full re-run of kpi_currency_probe.py (no "
            "randomness, no wall-clock reads besides the fixed run_date literal) against "
            "the unmodified evaluate_gate() import",
        "seed": "n/a -- deterministic, no stochastic seed",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY ad-hoc audit receipt under evidence/audit/kpi-claim-currency-v1/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.envelope-gates-kpi-claim-currency+json"
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
print("kpi_metric_is_currently_stale_and_false", diag["kpi_metric_is_currently_stale_and_false"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
