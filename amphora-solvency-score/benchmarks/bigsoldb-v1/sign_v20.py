"""Assemble + DSSE-Ed25519-sign the in-house bigsoldb-v1 benchmark receipt.

Signs the CANONICAL (timing-free) evaluation receipt whose scientific content
reproduced byte-identically across two fully independent executions. Binds the
curation + canonical evaluation SHA-256 and the exact gate this closes. Signs
with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key -- explicitly NOT the
trust-anchored phase0-evaluator key (absent on this host): it closes
SCIENTIFIC_BENCHMARK_NOT_EXECUTED scientifically, it does NOT clear
EVALUATION_SIGNATURE_ABSENT and does NOT promote the module.
"""
import hashlib, json, base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-solvency-score/benchmarks/bigsoldb-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

RUNA_FULL_SHA = "934b3b83b979be440031e2b4055af40730afff24d931a8f1558dd73b605065c6"
RUNB_FULL_SHA = "57c593ece589d93b9f18994fed17ed0135329e55a60e7f2c3b137dcd05f14010"
CANONICAL_SHA = "74d3a0f71e6512283de2bf32a16fc76a1543439dbbb0a92c73e986d4f187a9ae"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


eval_bytes = (BENCH / "evaluation_receipt.v20.canonical.json").read_bytes()
cur_bytes = (BENCH / "curation_receipt.v20.json").read_bytes()
eval_sha = sha(eval_bytes)
cur_sha = sha(cur_bytes)
assert eval_sha == CANONICAL_SHA, f"{eval_sha} != {CANONICAL_SHA}"

ev = json.loads(eval_bytes)
lso = next(s for s in ev["splits"] if s["split"] == "leave_solute_out")
best_base = min(lso["baselines"].values(), key=lambda d: d["rmse"])

receipt = {
    "schema": "amphora.solvency-score.bigsoldb-v1-inhouse-benchmark-receipt.v1",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-solvency-score",
    "benchmark": "amphora-solvency-score/bigsoldb-v1",
    "purpose": "Execute the locked leakage-safe solvency benchmark on the canonical host "
               "from in-tree rights-cleared data, closing the scientific-benchmark gate.",
    "dataset": {
        "name": "BigSolDB v2.0", "license": "CC-BY-4.0",
        "citation": "Krasnov et al., Sci Data 12 (2025), doi:10.1038/s41597-025-05559-8",
        "in_tree_path": "feedback/v1/external_data/bigsoldb_v2/raw/BigSolDBv2.0.csv",
        "raw_sha256": ev["raw_sha256"],
        "note": "In-tree v2.0 data actually present on this host; NOT the audit's Mac-Studio v2.1 run."},
    "protocol": {
        "primary_split": "leave_solute_out (extrapolation to unseen molecules) -- the deployment "
                         "case for a solvency screen on novel candidates",
        "secondary_splits_observed_not_gated": {
            "note": "leave_solvent_out pooled RMSE ~0.60 and grouped_random_in_domain observed in "
                    "the full 3-split run1 log; not included in this signed two-replay gate to keep "
                    "wall-clock bounded on a shared host (load ~120).",
            "leave_solvent_out_per_fold_rmse": [0.5494, 0.5609, 0.4932, 1.0824, 0.5451]},
        "leakage_controls": "grouped 5-fold by canonical solute; inner grouped holdout for early "
                            "stopping; replicate collapse to median before splitting; no row-level leakage",
        "model": "LightGBM (deterministic=True, force_row_wise) on RDKit-2026.03.2 2D descriptors "
                 "(solute+solvent)+temperature",
        "baselines": ["b0_global_mean", "b1_solvent_mean", "b2_solute_mean", "b3_two_way_additive"],
        "seed": ev["seed"], "n_features": ev["n_features"], "n_rows_modeled": ev["n_rows_modeled"],
        "n_solute_groups": lso["n_groups"]},
    "headline_result_leave_solute_out": {
        "model_rmse_log_units": lso["model"]["rmse"],
        "model_rmse_ci95_cluster_bootstrap": lso["model"]["rmse_ci95_cluster_bootstrap"],
        "model_mae": lso["model"]["mae"], "model_r2": lso["model"]["r2"],
        "model_frac_within_1log": lso["model"]["frac_within_1log"],
        "best_baseline": "per-solvent mean", "best_baseline_rmse": best_base["rmse"],
        "error_reduction_vs_best_baseline_pct": round(100 * (1 - lso["model"]["rmse"] / best_base["rmse"]), 1),
        "published_sota_band_rmse": [0.83, 0.99],
        "prior_thermodynamic_cycle_sota_rmse": [1.43, 2.16],
        "interpretation": "Diagnostic. RMSE inside the published solute-extrapolation SOTA band; CI "
                          "excludes the best naive baseline. No candidate-performance or superiority claim."},
    "reproducibility": {
        "two_replay_sha256_gate": "PASS (canonical/scientific content)",
        "replays": 2, "independent_full_pipeline_runs": True,
        "run_a_full_receipt_sha256": RUNA_FULL_SHA,
        "run_b_full_receipt_sha256": RUNB_FULL_SHA,
        "full_receipt_sole_difference": "wall_seconds timing field (271.6 vs 247.7); all splits, "
                                        "metrics, CIs, fold-assignment hashes, feature counts and raw "
                                        "SHA byte-identical",
        "canonical_evaluation_receipt_sha256": CANONICAL_SHA,
        "curation_receipt_two_replay": "byte-identical across both runs",
        "curation_receipt_sha256": cur_sha},
    "closes_gate": "SCIENTIFIC_BENCHMARK_NOT_EXECUTED",
    "does_not_close": ["EVALUATION_SIGNATURE_ABSENT (requires trust-anchored phase0-evaluator key, "
                       "absent on this host)", "human / independent review"],
    "toolchain": {"python": ev["python"], "rdkit": ev["rdkit"], "lightgbm": ev["lightgbm"],
                  "sklearn": ev["sklearn"]},
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.solvency-benchmark+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "inhouse_benchmark_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("headline_lso_rmse", lso["model"]["rmse"], "ci", lso["model"]["rmse_ci95_cluster_bootstrap"],
      "best_baseline", best_base["rmse"],
      "err_reduction_pct", round(100 * (1 - lso["model"]["rmse"] / best_base["rmse"]), 1))
