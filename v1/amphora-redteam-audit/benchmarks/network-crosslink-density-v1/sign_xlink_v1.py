#!/usr/bin/env python3
"""DSSE-Ed25519-sign the network-crosslink-density-v1 AUDIT_ONLY diagnostic.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (NOT a trust-anchored phase0 key). Promotes
nothing; signs no phase0 evaluation/review receipt; modifies no existing
receipt, the manifest, or the signed v1/v2/v3 network-Tg audits.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

REPO = Path(__file__).resolve().parents[3]
BENCH = REPO / "amphora-redteam-audit/benchmarks/network-crosslink-density-v1"
KEY = REPO / ".amphora/control/local-ed25519.key"
PUB = json.loads((REPO / ".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "c63cfdee3e3d21402b9f9014745948b146bdac054589c3d0cf44871443413eef"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "network_xlink_v1_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.network-crosslink-density-rubber-elasticity-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "NETWORK_CROSSLINK_DENSITY_COMPLEMENTARY_AXIS_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/network-crosslink-density-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "target_kpi_id": diag["target_kpi_id"],
    "predecessor": diag["predecessor"],
    "supersedes_nothing": True,
    "purpose": (
        "AUDIT_ONLY red-team science increment on the HIGHEST-value UNVALIDATED coating gap: "
        "the glass transition AND network stiffness of marine DGEBA + amine networks. The signed "
        "v3 backbone-rigidity descriptor reached LOO Tg MAE 35.73 C and DIAGNOSED that connectivity "
        "cannot encode the crosslink-functionality boost lifting polyfunctional TETA (6 N-H) and "
        "DETA (5 N-H) above the tetrafunctional diamines. This run BUILDS that missing physics "
        "from first principles -- the a-priori Flory perfect-network crosslink strand density "
        "n_x [mol/kg] from the amine SMILES + DGEBA molar mass ONLY (measured Tg never a feature) "
        "-- and tests it NON-CIRCULARLY on the SAME page-verified rights-clean n=9/7-unique data. "
        "Result: n_x is the physically-correct COMPLEMENTARY axis (it uniquely explains the "
        "TETA/DETA under-prediction; exclDDS Spearman(n_x, B-residual)=0.49) and its rubber-"
        "elasticity rubbery modulus E'=3 nu_c R T lands entirely in the textbook epoxy band "
        "(43.5-65.3 MPa in 10-100). BUT the 2-feature (B + n_x) LOO does NOT reduce held-out Tg "
        "MAE (35.73 -> 48.96 C, honest overfit on n=7 with a single aromatic outlier): the binding "
        "constraint is DATA QUANTITY (n>=12), not missing descriptors. Sharper founder conclusion: "
        "BOTH governing non-circular descriptors are now in hand; the sole blocker to a Phase-0 Tg "
        "KPI is rights-clean DATA VOLUME, and a point-validated rubbery-MODULUS KPI is data-rights-"
        "blocked (no accessible CC-BY measured-modulus truth this run), not theory-blocked. "
        "ADVANCED / PHYSICAL_CONSISTENCY only; NOT a Phase-0 promotion."),
    "theory": diag["theory"],
    "constants": diag["constants"],
    "n_unique_systems": len(diag["unique_systems"]),
    "n_measurements": len(diag["raw_measurements"]),
    "correlations": diag["correlations"],
    "loo_summary": {k: {"loo_mae_C": v["loo_mae_C"], "loo_rmse_C": v["loo_rmse_C"], "loo_bias_C": v["loo_bias_C"]}
                    for k, v in diag["loo"].items()},
    "null_baselines": diag["null_baselines"],
    "residual_analysis_key": {
        "pearson_n_x_vs_B_residual_all7": diag["residual_analysis"]["pearson_n_x_vs_B_residual_all7"],
        "spearman_n_x_vs_B_residual_exclDDS": diag["residual_analysis"]["spearman_n_x_vs_B_residual_exclDDS_aromatic_outlier"],
        "reading": diag["residual_analysis"]["reading"]},
    "rubber_elasticity_consistency": diag["rubber_elasticity_consistency"],
    "phase0_gates": diag["phase0_gates"],
    "phase0_reconciliation_redteam": diag["phase0_reconciliation_redteam"],
    "verdict": diag["verdict"],
    "honest_limitations": diag["honest_limitations"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "code_path_independence": "single Python+RDKit harness, two independent executions (honest scope)",
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": harness_sha,
        "v3_B_only_LOO_reproduced_exactly_C": diag["loo"]["B_only"]["loo_mae_C"],
        "rdkit_version": "2026.03.2",
    },
    "does_not_close": diag["does_not_close"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-network-crosslink-density+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("canonical_diagnostic_sha256", CANONICAL_SHA)
