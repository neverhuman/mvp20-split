#!/usr/bin/env python3
"""DSSE-Ed25519-sign the network-tg-feasibility-v4 AUDIT_ONLY diagnostic.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (NOT a trust-anchored phase0 key). Promotes
nothing; signs no phase0 evaluation/review receipt; modifies no existing
receipt, the manifest, or the signed v1/v2/v3 network-Tg or crosslink audits.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

REPO = Path(__file__).resolve().parents[3]
BENCH = REPO / "amphora-redteam-audit/benchmarks/network-tg-feasibility-v4"
KEY = REPO / ".amphora/control/local-ed25519.key"
PUB = json.loads((REPO / ".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "97e4ada7dc27591205a7cecf026ff25f2befe55af3ff8bcc866245b408db5e5d"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "network_tg_v4_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.network-tg-protocol-curation-feasibility-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "NETWORK_TG_PROTOCOL_CURATION_FEASIBILITY_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/network-tg-feasibility-v4",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "target_kpi_id": diag["target_kpi_id"],
    "predecessor": diag["predecessor"],
    "supersedes_nothing": True,
    "purpose": (
        "AUDIT_ONLY red-team science increment on the HIGHEST-value UNVALIDATED coating gap: the "
        "glass transition temperature of marine DGEBA + amine networks. Prior signed runs built "
        "the two governing non-circular descriptors (backbone rigidity B, Flory crosslink density "
        "n_x) and asserted 'acquire n>=12'. This run adds two quantified, decision-relevant "
        "findings from page-verified CC-BY evidence gathered this run. (1) CURE-STATE PROTOCOL "
        "SENSITIVITY: the SAME amine's Tg shifts 27-46 C purely with cure state (IPDA full 158 vs "
        "cold 112; DDS post-cured 208 vs hot-cure reference 181, MDPI Polymers 2023 15(4)990 = "
        "PMC9962791, CC BY) -- LARGER than the <=25 C G2 gate. Since the gate sits ABOVE the "
        "~8.6 C same-protocol inter-lab floor but BELOW the 27-46 C cross-cure-state scatter, the "
        "network-Tg KPI is achievable ONLY on a protocol-CONTROLLED rights-clean dataset; naive "
        "aggregation of open-literature Tg can never reach it. (2) MODEL STRUCTURAL CEILING: the "
        "linear B+n_x model already has ~26 C in-sample RMSE (R2 0.55) at n=7, so more data "
        "de-leverages the LOO but cannot cross <=25 C without a steric/side-group descriptor "
        "(IPDA gem-dimethyl; DDS sulfone) or a nonlinear model. Verdict: co-limited by protocol "
        "curation AND model form; NOT a Phase-0 promotion. Reproduces v3 (35.73 C) and "
        "crosslink-v1 (48.96 C) LOO exactly as internal cross-checks."),
    "theory": diag["theory"],
    "constants": {"DGEBA_smiles": diag["DGEBA_smiles"], "EEW_DGEBA": diag["EEW_DGEBA"],
                  "M_DGEBA": diag["M_DGEBA"]},
    "protocol_consistent_training_set_summary": {
        "n_unique_systems": diag["protocol_consistent_training_set"]["n_unique_systems"],
        "n_measurements": diag["protocol_consistent_training_set"]["n_measurements"],
        "independent_sources": diag["protocol_consistent_training_set"]["independent_sources"],
        "classes_spanned": diag["protocol_consistent_training_set"]["classes_spanned"]},
    "cross_protocol_evidence_not_merged": diag["cross_protocol_evidence_not_merged"],
    "protocol_sensitivity": diag["protocol_sensitivity"],
    "gate_feasibility": diag["gate_feasibility"],
    "models": diag["models"],
    "data_requirement": diag["data_requirement"],
    "acquisition_log": diag["acquisition_log"],
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
        "v3_B_only_LOO_reproduced_exactly_C": diag["models"]["loo_B_1axis"]["loo_mae_C"],
        "xlink_v1_2axis_LOO_reproduced_exactly_C": diag["models"]["loo_B_plus_nx_2axis"]["loo_mae_C"],
        "rdkit_version": "2026.03.2",
    },
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-network-tg-protocol-curation+json"
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
