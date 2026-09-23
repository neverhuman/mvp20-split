#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score Herschel-Bulkley CC-BY
real-data benchmark (campaign C9). AUDIT_ONLY: does NOT promote the module,
does NOT edit the signed FFW/melt-viscosity Phase-0 KPI, does NOT modify the
66-receipt master manifest, does NOT modify reference/rheology/source-landscape.v1.json."""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/audit/herschel-bulkley-ccby-amorim2021-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


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


canon = (EV / "diagnostic.canonical.json").read_bytes()
runB = (EV / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["all_corrected_gates_passed"] is True, "gates not all passed"

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_hb_benchmark.py"), str(third)], check=True, cwd=str(EV))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_hb_benchmark.py").read_bytes())
source_lock_sha = sha((EV / "source_amorim2021_hb_table2.v1.json").read_bytes())
assert source_lock_sha == diag["source_lock_sha256"], "source lock hash mismatch"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text()) if TRUST.exists() else {"keys": []}
tbr = {k.get("role"): k for k in trust.get("keys", [])}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.viscosity-score.herschel-bulkley-ccby-benchmark-receipt.v1",
    "receipt_id": "herschel-bulkley-ccby-amorim2021-v1",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-01",
    "generated_on_host": "xbabe2",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_source_landscape": False,
    "campaign_item_id": "C9",
    "claim_under_attack": diag["claim_under_attack"],
    "scope_of_this_run": diag["scope_of_this_run"],
    "claim": (
        "First real-data benchmark of amphora-viscosity-score's HERSCHEL_BULKLEY "
        "path (src/lib.rs:1227). A rights-clean CC BY 4.0 published source "
        "(Amorim et al. 2021, SN Applied Sciences 3:236, doi:10.1007/s42452-021-04247-7) "
        "supplies Herschel-Bulkley fitted parameters (tau_0, K, n; R^2>0.998) for a "
        "commercial DGEBA epoxy / polyamide anti-corrosion coating, control + 5 "
        "carbon-black/nanoclay formulations. The module's exact HB equation, "
        "independently re-derived in Python and evaluated at these published "
        "parameters across the paper's own experimental shear-rate domain "
        "(0.1-100 /s), reproduces apparent-viscosity values inside the paper's own "
        "stated Fig.3 axis bounds (1 to 1e5 Pa.s) for all 6 formulations, is "
        "monotonically shear-thinning (n<1 for all 6, matching the paper's stated "
        "finding), and reproduces the paper's own ranking claims (sample 4 = max "
        "yield stress, unmodified control = min consistency coefficient) -- ONLY "
        "after repairing a genuine locale decimal-separator ambiguity in the "
        "as-printed table (every tau_0/K value is typeset with a comma before the "
        "final 3 digits while n/R2/MRD use a period, a Word/Excel-to-PDF locale "
        "mixup). The naive literal-English reading of the SAME as-printed table "
        "(comma = thousands separator, i.e. what a downstream engineer would "
        "transcribe verbatim) fails the paper's own axis bounds by 13x-169x for "
        "every one of the 6 formulations -- this IS the falsifying observation the "
        "attack was designed to surface, and it occurred, just not for the "
        "corrected/justified reading. KRIEGER_DOUGHERTY remains unbenchmarked: no "
        "rights-clean pigment/filler volume-fraction viscosity ladder was found "
        "this fire despite an extensive open-literature sweep (MDPI Coatings/"
        "Polymers, RSC Advances, ACS Omega, Scientific Reports, Frontiers, SN "
        "Applied Sciences); filed as a data-acquisition-queue ask."),
    "theory_reference": (
        "Herschel, W.H. & Bulkley, R. (1926) 'Konsistenzmessungen von "
        "Gummi-Benzollosungen', Kolloid-Zeitschrift 39:291-300. "
        "eta_apparent(gamma_dot) = tau_0/gamma_dot + K*gamma_dot^(n-1)."),
    "source": {
        "source_id": diag["source_id"],
        "doi": diag["source_doi"],
        "license": diag["source_license"],
        "source_lock_sha256": diag["source_lock_sha256"],
    },
    "results": {
        "shear_rates_tested_s_inv": diag["shear_rates_tested_s_inv"],
        "paper_axis_bounds_pa_s": diag["paper_axis_bounds_pa_s"],
        "rows": diag["rows"],
        "literal_english_reading_all_within_axis_bounds": diag["literal_english_reading_all_within_axis_bounds"],
        "corrected_reading_all_within_axis_bounds": diag["corrected_reading_all_within_axis_bounds"],
        "corrected_reading_all_monotonic_decreasing": diag["corrected_reading_all_monotonic_decreasing"],
        "corrected_reading_all_shear_thinning_n_lt_1": diag["corrected_reading_all_shear_thinning_n_lt_1"],
        "sample4_has_max_tau0_corrected": diag["sample4_has_max_tau0_corrected"],
        "epoxy_control_has_min_K_corrected": diag["epoxy_control_has_min_K_corrected"],
        "all_corrected_gates_passed": diag["all_corrected_gates_passed"],
    },
    "refutation_criterion": diag["refutation_criterion"],
    "verdict": "CLAIM_SURVIVED",
    "verdict_detail": diag["verdict"],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "harness_sha256": {"run_hb_benchmark.py": harness_sha},
        "source_lock_sha256": source_lock_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "byte_identical": canon == runB,
        "determinism": "pure-python arithmetic re-derivation of src/lib.rs:1227, no RNG, no network at run time (source table hash-locked).",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY benchmark receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-herschel-bulkley-ccby-benchmark+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "herschel-bulkley-ccby-amorim2021-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
