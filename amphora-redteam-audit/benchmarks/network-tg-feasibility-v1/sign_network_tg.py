"""DSSE-Ed25519-sign the network-Tg feasibility audit diagnostic.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. AUDIT_ONLY red-team feasibility study: promotes
nothing, signs no phase0 evaluation/review receipt, modifies no existing
receipt or manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/network-tg-feasibility-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "902cf6738f91589e324d49b6634e37007123f1736a4baa91ade2e576d6fc836b"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "network_tg_feasibility_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.network-tg-feasibility-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "NETWORK_TG_PREDICTION_FEASIBILITY_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/network-tg-feasibility-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "target_kpi_id": diag["target_kpi_id"],
    "purpose": (
        "Independent (Python+RDKit) red-team feasibility audit of glass-transition-"
        "temperature prediction for stoichiometric DGEBA-amine marine-coating networks. "
        "Reproduces (by citing the signed in-tree receipts) that the incumbent "
        "polyuniverse-trained ML (MAE 39.1 C, r~0.08) and raw Van Krevelen (MAE 109.1 C) "
        "BOTH FAIL on the 5 canonical network systems; identifies and prototypes the "
        "correct physics -- exact NON-CIRCULAR crosslink density (from the verified "
        "EEW/AHEW core) plus ring/rotatable-bond backbone rigidity -- and honestly "
        "quantifies why this is NOT yet a Phase-0 KPI (rights-clean cited Tg is n=5, "
        "single-source, +/-20-30 C inter-lab scatter)."),
    "theory": diag["theory"],
    "EEW_DGEBA": diag["EEW_DGEBA"],
    "incumbent_state_from_signed_receipts": diag["incumbent_state_from_signed_receipts"],
    "correlations_cited5": diag["correlations_cited5"],
    "correlations_all10_direction_only": diag["correlations_all10_direction_only"],
    "physical_model_loo": diag["physical_model_loo"],
    "phase0_gates_for_a_real_tg_kpi": diag["phase0_gates_for_a_real_tg_kpi"],
    "verdict": diag["verdict"],
    "honest_limitations": diag["honest_limitations"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "code_path_independence": "single Python+RDKit harness, two independent executions "
            "(NOT dual-language; honest scope)",
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "does NOT promote amphora-molecule-property (or any module) to PHASE_0",
        "does NOT change the defensible Phase-0 count, which remains 10 (9 infrastructure "
        "+ amphora-solvency-score, the sole promoted science module)",
        "does NOT claim a fitted Tg KPI; n=5 rights-clean cited systems is below the bar",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-network-tg-feasibility+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
