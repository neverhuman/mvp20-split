#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score KRIEGER_DOUGHERTY CC-BY
reachability-probe finding (campaign W-VISC1, fire 1). AUDIT_ONLY: does not
promote the module, does not touch the C9 fire 1 HERSCHEL_BULKLEY receipt/KPI
or the C9 fire 2 Reynolds-2024 BLOCKED_RIGHTS receipt/verdict (both remain
independently valid and unmodified), does not modify the 66-receipt master
manifest, does not extract or reproduce any data from the still-rights-
blocked Reynolds et al. 2024 source."""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/phase0/repairs/W-VISC1/attempts/krieger-dougherty-ccby-reachability-probe-v1"
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
assert diag["verdict"] == "CLAIM_REFUTED"

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_kd_ccby_reachability_probe.py"), str(third)],
                check=True, cwd=str(EV))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_kd_ccby_reachability_probe.py").read_bytes())
fig8_sha = sha((EV / "fig8.jpg").read_bytes())
assert fig8_sha == diag["fig8_source_image_sha256"], "fig8 image hash mismatch"

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
    "schema": "amphora.viscosity-score.krieger-dougherty-ccby-reachability-probe-receipt.v1",
    "receipt_id": "krieger-dougherty-ccby-reachability-probe-v1",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-05",
    "generated_on_host": "xbabe2 (search performed from xbabe1 via WebSearch/WebFetch)",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_c9_fire1_herschel_bulkley_receipt": False,
    "modifies_c9_fire2_reynolds2024_rights_wall_receipt": False,
    "campaign_item_id": "W-VISC1",
    "claim_under_attack": diag["claim_under_attack"],
    "supersedes": {
        "superseded_path": "amphora-viscosity-score/evidence/audit/krieger-dougherty-rights-wall-reynolds2024-v1/krieger-dougherty-rights-wall-reynolds2024-receipt.v1.dsse.json",
        "superseded_sha256": None,  # filled below once computed
        "superseded_deleted_or_modified": False,
        "reason": (
            "C9 fire 2 established Reynolds et al. 2024 as the only reachable eta-vs-phi candidate "
            "and, finding it CC BY-NC-ND, issued a BLOCKED_RIGHTS verdict on the underlying claim that "
            "KRIEGER_DOUGHERTY is 'benchmarkable against real data with current in-tree assets'. That "
            "specific finding (Reynolds 2024 is rights-blocked) remains TRUE and UNCHANGED here. This "
            "receipt does not retract it. It supersedes only the broader downstream inference -- stated "
            "as this campaign item's claim_text -- that 'the Krieger-Dougherty implementation cannot be "
            "benchmarked against ANY rights-clean dataset currently reachable'. That broader claim is "
            "REFUTED by this fire: a second, independent, unambiguously CC BY 4.0 on-scope candidate "
            "(Finke et al. 2021) was found and a full benchmark WAS run against it, with an honestly "
            "disclosed underpowered/non-identifiable result."
        ),
    },
    "search_record_this_fire": diag["sources_checked_this_fire"],
    "digitization_method": {
        "source_image": "materials-14-02752-g008.jpg (Fig. 8 of Finke et al. 2021, CC BY 4.0)",
        "source_image_sha256": fig8_sha,
        "technique": "pixel-centroid colour-cluster detection with log-log axis calibration from "
                     "detected plot-border pixels, cross-checked against 4x-zoomed visual crop "
                     "inspection of the same regions; ambiguous/overlapping clusters excluded rather "
                     "than guessed (see digitized_data_points_excluded in the diagnostic).",
        "points_used": diag["digitized_data_points_used"],
        "points_excluded": diag["digitized_data_points_excluded"],
    },
    "density_assumption": diag["density_assumption"],
    "shear_rate_choice": diag["shear_rate_choice"],
    "benchmark_result": {
        "central_density_fit_result": diag["central_density_fit_result"],
        "density_sensitivity_free_intrinsic_fit": diag["density_sensitivity_free_intrinsic_fit"],
    },
    "refutation_criterion": diag["refutation_criterion"],
    "interpretation": diag["interpretation"],
    "verdict": "CLAIM_REFUTED",
    "verdict_scope": diag["verdict_scope"],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "harness_sha256": {"run_kd_ccby_reachability_probe.py": harness_sha},
        "fig8_source_image_sha256": fig8_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "byte_identical": canon == runB,
        "determinism": "pure-python digitized-value fit (scipy curve_fit + seeded "
                        "differential_evolution, seed=1), no network I/O at run time.",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY reachability-probe receipt under evidence/phase0/repairs/W-VISC1/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}

# fill in superseded_sha256 now that we can read the prior receipt
prior = ROOT / body_obj["supersedes"]["superseded_path"]
body_obj["supersedes"]["superseded_sha256"] = sha(prior.read_bytes())

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-krieger-dougherty-ccby-reachability-probe+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "krieger-dougherty-ccby-reachability-probe-receipt.v1.dsse.json"
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
