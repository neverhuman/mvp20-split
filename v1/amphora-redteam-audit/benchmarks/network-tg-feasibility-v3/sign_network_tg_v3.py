"""DSSE-Ed25519-sign the network-tg-feasibility-v3 audit diagnostic.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. AUDIT_ONLY red-team science increment: promotes
nothing, signs no phase0 evaluation/review receipt, modifies no existing
receipt or manifest, and does NOT touch the signed v1/v2 audits.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/network-tg-feasibility-v3")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "daee7708cb5d02a54237c16deac90f88c08bbc9159aaf89e5d5539d976bc812b"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "network_tg_v3_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.network-tg-feasibility-v3-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "NETWORK_TG_BACKBONE_RIGIDITY_DESCRIPTOR_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/network-tg-feasibility-v3",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "target_kpi_id": diag["target_kpi_id"],
    "predecessor": diag["predecessor"],
    "supersedes_nothing": True,
    "purpose": (
        "AUDIT_ONLY red-team increment on the HIGHEST-value UNVALIDATED gap: glass-transition "
        "temperature of marine-coating DGEBA + amine networks. v2 REFUTED whole-molecule "
        "structure-only descriptors and diagnosed that they cannot separate BACKBONE-rigid "
        "(DDS: aromatic rings IN the crosslink path, Tg 208) from PENDANT/HINGE-rigid (m-XDA: "
        "aromatic ring flanked by rotatable -CH2-, Tg 100) at nearly equal whole-molecule "
        "aromatic fraction. This run BUILDS the topological backbone N-to-N rigid-bond-fraction "
        "descriptor v2 called for and tests it NON-CIRCULARLY on the SAME page-verified "
        "rights-clean n=9/7-unique data (no new/fabricated data). Result: the first structure-"
        "only model to beat the incumbent ML (LOO 35.7 vs 39.1 C) and the LOO-NULL, improving "
        "best LOO MAE 40.5->35.7 C and correctly ranking the two highest-Tg systems; but it "
        "still FAILS the >=25 C KPI gate and the n>=12 data gate. Honest ADVANCED_NOT_VALIDATED "
        "status; NOT a Phase-0 gate."),
    "theory": diag["theory"],
    "data_ceiling_honesty": diag["data_ceiling_honesty"],
    "n_unique_systems": len(diag["unique_consensus_systems"]),
    "n_measurements": len(diag["raw_measurements"]),
    "correlations_pearson_unique7": diag["correlations_pearson_unique7"],
    "null_baselines": diag["null_baselines"],
    "leave_one_system_out_summary": {
        k: {"loo_mae_C": v["loo_mae_C"], "loo_rmse_C": v["loo_rmse_C"], "loo_bias_C": v["loo_bias_C"]}
        for k, v in diag["leave_one_system_out"].items()},
    "leave_one_SOURCE_out_backbone": diag["leave_one_SOURCE_out_backbone"],
    "incumbent_state_from_signed_receipts": diag["incumbent_state_from_signed_receipts"],
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
        "ring_only_reproduction_of_v2": "40.505739 C reproduced EXACTLY (independent-implementation cross-check of the LOO pipeline vs signed v2)",
        "rdkit_version": "2026.03.2",
    },
    "does_not_close": [
        "does NOT promote amphora-molecule-property (or any module) to PHASE_0; G1 (n>=12) and "
        "G2 (LOO<=25 C) remain UNMET",
        "does NOT add any PHASE_0 module. Live module-manifest reconciliation (this run): 0 of 29 "
        "modules are scientific_readiness=VALIDATED; all are MODEL_READINESS_ONLY. 'FULL Phase-0' "
        "is a governance milestone, not validated science.",
        "does NOT modify any of the 66 signed receipts, the manifest, or the signed v1/v2 audits",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key only)",
        "does NOT fabricate or web-summarize any Tg value (unverified web-summary values REJECTED)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-network-tg-backbone-rigidity+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
