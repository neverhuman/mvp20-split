#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score FFW-vs-ML uncertainty-
disclosure-gap finding (ROTATION-mode fire, fire_id
20260803T060002-2746547-be6ffcedb651). AUDIT_ONLY: does NOT promote the
module, does NOT edit the FFW-vs-ML or conformal+AD Phase-0 KPI receipts or
docs/mission.md, does NOT modify the 66-receipt master manifest, does NOT
extract or reproduce any row-level data from the quarantined Polyverse
dataset -- only already-signed downstream JSON KPI/receipt bytes were read."""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/audit/ffw-vs-ml-uncertainty-disclosure-gap-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260803T060002-2746547-be6ffcedb651"


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
assert diag["verdict"] == "REFUTED", f"unexpected verdict {diag['verdict']}"
assert diag["results"]["disclosure_gap_confirmed"] is True

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_ffw_uncertainty_disclosure_audit.py"), str(third)],
               check=True, cwd=str(EV))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_ffw_uncertainty_disclosure_audit.py").read_bytes())

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
    "schema": "amphora.viscosity-score.ffw-vs-ml-uncertainty-disclosure-gap-receipt.v1",
    "receipt_id": "ffw-vs-ml-uncertainty-disclosure-gap-v1",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "mode": "ROTATION",
    "fire_id": FIRE_ID,
    "date": "2026-08-03",
    "scientific_success_required_for_phase0": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_mission_md": False,
    "modifies_signed_phase0_kpi": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "derives_from_quarantined_row_data": False,
    "claim_under_attack": (
        "amphora-viscosity-score/evidence/phase0/kpis/"
        "polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-"
        "kpi.v1.json :: headline finding 'best_physical_ffw_baseline_beats_"
        "ml_r2_documented' (physical B3 R^2=+0.5972 beats ML B4 R^2=+0.4536 "
        "by +0.1436, claim_lock physics_wins_ml_loses_documented_honestly="
        "true) is presented as an honestly and completely documented Phase-0 "
        "empirical finding."
    ),
    "attack": (
        "Methodological uncertainty-disclosure audit: cross-referenced the "
        "FFW-vs-ML KPI against its own sibling KPI on the IDENTICAL seed=0 "
        "polymer-safe 60/20/20 partition (41 train / 13 test unique polymers, "
        "863/194 rows) -- the polymer-safe conformal+applicability-domain KPI "
        "-- confirming the shared partition via the FFW receipt's own "
        "conformal_receipt_sha256 cross-link field. Ran a positive-control "
        "arithmetic self-consistency check (RMSE^2/(1-R^2) must imply an "
        "identical SS_tot/n across all 5 baselines scored on the same test "
        "set) to confirm the underlying numbers are NOT being disputed. Then "
        "exhaustively scanned the FFW KPI's full JSON body for any token "
        "indicating quantified estimation uncertainty (bootstrap, confidence "
        "interval, cluster, jackknife, standard error) and found none, versus "
        "the sibling KPI which explicitly documents its own small-n "
        "conditional-coverage collapse (worst applicability-domain quintile "
        "coverage 0.379 vs marginal 0.897) and its R^2 gap versus the parent "
        "model (0.4535 vs 0.944). Compared both to the published cluster-"
        "count-adequacy threshold for reliable inference (Cameron, Gelbach & "
        "Miller 2008; Cameron & Miller 2015): the FFW KPI's headline "
        "comparison rests on only 13 independent test-polymer clusters, well "
        "below the field's own G>=~30 rule-of-thumb minimum, with zero "
        "acknowledgement of that fragility anywhere in the KPI. Reads only "
        "already-signed, non-quarantined downstream KPI/receipt JSON bytes -- "
        "does not open, parse, or derive any value from the underlying "
        "quarantined Polyverse melt-viscosity row-level CSV, the same "
        "governance boundary already accepted for this module's "
        "polyverse-rights-disclosure-gap-v1 audit."
    ),
    "refutation_criterion": (
        "The claim SURVIVES if the FFW-vs-ML KPI discloses estimation "
        "uncertainty (bootstrap, CI, cluster-count caveat, or equivalent) for "
        "its headline R^2 gap at a standard comparable to its own sibling "
        "conformal+AD KPI on the identical partition, OR if 13 independent "
        "test-chemistry clusters meets accepted cluster-count-adequacy "
        "thresholds for the comparison being made. It is REFUTED if: (1) both "
        "KPIs are confirmed to share the identical seed=0 polymer-safe "
        "partition via matching receipt hashes; (2) the FFW KPI's own R^2/"
        "RMSE numbers are internally self-consistent (so the finding is not "
        "being disputed on arithmetic grounds); (3) the FFW KPI JSON body "
        "contains zero tokens indicating any quantified uncertainty measure; "
        "(4) the sibling KPI on the same partition DOES document an "
        "equivalent small-n/conditional-coverage caveat about itself; and (5) "
        "the test cluster count (13 unique polymers) is below the published "
        "G>=~30 threshold for reliable cluster-level inference."
    ),
    "verdict": diag["verdict"],
    "results": diag["results"],
    "headline_result": {
        "same_partition_confirmed": diag["results"]["same_partition_confirmed"],
        "ffw_r2_gap_numerically_self_consistent": diag["results"]["ffw_r2_gap_numerically_self_consistent"],
        "ffw_kpi_discloses_zero_uncertainty_quantification": diag["results"]["ffw_kpi_discloses_zero_uncertainty_quantification"],
        "sibling_kpi_on_same_partition_discloses_conditional_gap": diag["results"]["sibling_kpi_on_same_partition_discloses_conditional_gap"],
        "test_cluster_count_below_published_inference_threshold": diag["results"]["test_cluster_count_below_published_inference_threshold"],
        "n_test_polymers": diag["cluster_count_audit"]["n_test_polymers"],
        "n_test_rows": diag["cluster_count_audit"]["n_test_rows"],
        "interpretation": diag["interpretation"],
    },
    "numeric_self_consistency_positive_control": diag["numeric_self_consistency_positive_control"],
    "cluster_count_audit": diag["cluster_count_audit"],
    "disclosure_comparison": diag["disclosure_comparison"],
    "theory": [
        "Papadopoulos, Proedrou, Vovk & Gammerman (2002) split conformal "
        "prediction -- the theoretical basis the module's own sibling KPI "
        "correctly cites for why only MARGINAL, not conditional, coverage is "
        "guaranteed.",
        "Cameron, A.C., Gelbach, J.B. & Miller, D.L. (2008) 'Bootstrap-Based "
        "Improvements for Inference with Clustered Errors', Review of "
        "Economics and Statistics 90(3):414-427.",
        "Cameron, A.C. & Miller, D.L. (2015) 'A Practitioner's Guide to "
        "Cluster-Robust Inference', Journal of Human Resources 50(2):317-372.",
        "Fox & Flory 1948, Whitten 1954, Berry & Fox 1968, Ferry 1980 -- the "
        "physical scaling theory under comparison (unaffected by this audit).",
    ],
    "does_not_close": diag["does_not_close"],
    "human_action_needed": (
        "If the FFW-vs-ML 'physics beats ML' finding is to remain a headline "
        "Phase-0 empirical claim, amend the KPI (or a companion diagnostic) to "
        "disclose the same class of small-n/uncertainty caveat the module "
        "already applies to the sibling conformal+AD KPI on the identical "
        "partition -- e.g. a leave-one-polymer-out jackknife of the R^2 gap, "
        "or an explicit statement that the comparison rests on 13 independent "
        "chemistries and has not been resampled. This is a documentation/"
        "methodology completeness action, not a data-rights action (unlike "
        "the module's separate, still-open Polyverse rights-disclosure gap)."
    ),
    "provenance": {
        "harness_sha256": {"run_ffw_uncertainty_disclosure_audit.py": harness_sha},
        "inputs_sha256": diag["inputs_sha256"],
    },
    "reproducibility": {
        "byte_identical": True,
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "determinism": (
            "pure-python re-derivation from already-in-tree, already-hashed "
            "JSON files; no RNG, no network, no wall-clock reads at run time."
        ),
    },
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": eval_pin,
        "used_for": "AUDIT_ONLY ffw-vs-ml-uncertainty-disclosure-gap receipt under evidence/audit/",
    },
    "reviewer_reference": {
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "role": "PHASE0_INTERNAL_REVIEWER",
        "derives_pinned_trust_store_key_id": rev_pin,
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-ffw-vs-ml-uncertainty-disclosure-gap+json"
sig = eval_sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": {
        "payload": base64.standard_b64encode(body).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id, "sig": sig_b64}],
    },
}
out = EV / "ffw-vs-ml-uncertainty-disclosure-gap-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
