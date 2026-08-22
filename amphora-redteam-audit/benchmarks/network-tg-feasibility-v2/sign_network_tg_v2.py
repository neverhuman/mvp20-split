"""DSSE-Ed25519-sign the network-Tg feasibility v2 (expanded-data red-team) audit.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. AUDIT_ONLY red-team study: promotes nothing, signs no
phase0 evaluation/review receipt, modifies no existing receipt/manifest, and does
NOT modify the signed network-tg-feasibility-v1 audit.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/network-tg-feasibility-v2")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "c4fe7cb366f2fde8f1fb2169ea2795d2ad7465bcf6666ac744159273b3fbea74"


def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "network_tg_expanded_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.network-tg-feasibility-v2-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "NETWORK_TG_EXPANDED_DATA_REDTEAM_CORRECTION",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/network-tg-feasibility-v2",
    "predecessor_untouched": "amphora-redteam-audit/benchmarks/network-tg-feasibility-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "target_kpi_id": diag["target_kpi_id"],
    "purpose": (
        "Red-team CORRECTION of the network-Tg feasibility claim. Genuinely acquires additional "
        "rights-clean, individually-cited experimental Tg for stoichiometric DGEBA+amine networks "
        "from 3 independent sources (n=5 single-source -> n=9 measurements / 7 unique systems, "
        "4 amine classes), including direct inter-lab scatter (DGEBA/DDS = 200/204/220 C). Re-tests "
        "the v1 structure-only physics model with leave-one-system-out, leave-one-SOURCE-out, and a "
        "NULL mean-Tg baseline. FINDING: the v1 optimism (ring r=+0.69, LOO ~24 C, 'one dataset away "
        "from a KPI') does NOT survive independent data; best LOO MAE is WORSE than a trivial "
        "mean-Tg baseline. Network-Tg is further from Phase-0 than v1 implied."),
    "theory": diag["theory"],
    "EEW_DGEBA": diag["EEW_DGEBA"],
    "data_acquisition_this_run": diag["data_acquisition_this_run"],
    "raw_measurements_n": diag["raw_measurements_n"],
    "unique_systems_n": diag["unique_systems_n"],
    "amine_classes": diag["amine_classes"],
    "independent_source_measurement_scatter": diag["independent_source_measurement_scatter"],
    "incumbent_state_from_signed_receipts": diag["incumbent_state_from_signed_receipts"],
    "correlations_unique7": diag["correlations_unique7"],
    "null_mean_Tg_baseline_MAE_C_on_unique7": diag["null_mean_Tg_baseline_MAE_C_on_unique7"],
    "leave_one_system_out": diag["leave_one_system_out"],
    "leave_one_SOURCE_out_generalization": diag["leave_one_SOURCE_out_generalization"],
    "best_model": diag["best_model"],
    "failure_analysis": diag["failure_analysis"],
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
        "does NOT claim a fitted Tg KPI; the model is refuted on independent data and G1 (n>=12) "
        "remains unmet",
        "does NOT modify the signed network-tg-feasibility-v1 audit or any of the 66 signed receipts",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-network-tg-feasibility-v2+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
