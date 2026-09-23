#!/usr/bin/env python3
"""DSSE-Ed25519-sign the owk-adhesion-and-phase0-redteam-v1 AUDIT_ONLY diagnostic.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS), using the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (NOT a trust-anchored phase0 key). Promotes
nothing; signs no phase0 evaluation/review receipt; modifies no existing
receipt, the manifest, or any of the 66 signed receipts.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

REPO = Path(__file__).resolve().parents[3]
BENCH = REPO / "amphora-redteam-audit/benchmarks/owk-adhesion-and-phase0-redteam-v1"
KEY = REPO / ".amphora/control/local-ed25519.key"
PUB = json.loads((REPO / ".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "27a7edcfd5955c19e29daf64dd7101ebe22d17fbf9739c2ad29b92d245caeab5"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "owk_phase0_audit.py").read_bytes())

pr = diag["phase0_reconciliation_redteam"]
eng = diag["owk_adhesion_engine"]

receipt = {
    "schema": "amphora.redteam-audit.owk-adhesion-and-phase0-redteam-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "OWK_ADHESION_ENGINE_AND_PHASE0_HONESTY_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/owk-adhesion-and-phase0-redteam-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "target_kpi_id": diag["target_kpi_id"],
    "predecessor": diag["predecessor"],
    "supersedes_nothing": True,
    "purpose": (
        "Two-part AUDIT_ONLY red-team. PART A (founder-facing honesty map, recomputed "
        "LIVE from on-host governance state) directly tests the claim 'we have FULL "
        "Phase-0' and REFUTES the equivalence with validated science: scientific_readiness "
        "== VALIDATED for 0 of 29 modules; even the crown-jewel solvency-score is "
        "LOCKED_INTERNAL; of the 10 PHASE_0 modules 7 are NOT_APPLICABLE (no science) and "
        "3 LOCKED_INTERNAL; and scientific_success_required_for_phase0 == false in ALL 29 "
        "benchmark-locks -> Phase-0 is a GOVERNANCE gate. Honest answer to 'can we move a "
        "PRE_PHASE_0 module into PHASE_0 this run': NO -- promotion needs two distinct "
        "trusted human-key signatures on a module-local movement event, which an autonomous "
        "cron holding only the LOCAL_DEVELOPMENT_AUDIT_ONLY key cannot and must not forge; "
        "and the 19 PRE_PHASE_0 modules each carry an unmet gate (6 data-rights-walled, 4 "
        "benchmark-not-executed, 9 eval-binding). PART B is a REAL new science increment "
        "opening the ADHESION axis (the coating 'big three' is barrier + Tg + adhesion, and "
        "adhesion had no engine): the Fowkes / Owens-Wendt-Kaelble dispersive geometric-mean "
        "combining rule -- the exact engine for coating<->substrate work of adhesion and "
        "interfacial water resistance (cathodic-disbondment relevance) -- VALIDATED on the "
        "public-domain Fowkes (1964) water/n-alkane dataset: recovered gamma_w^d = 21.96 +/- "
        "0.63 mN/m across 7 aliphatics (literature 21.8), non-circular leave-one-out "
        "interfacial-tension MAPE 1.04%%, with all 3 non-dispersive controls (benzene/toluene/"
        "CCl4) correctly rejected at >3 sigma. In-scope application: Young-Dupre water work of "
        "adhesion 107.2 mN/m on a cured DGEBA+DDS marine epoxy from a CC BY 4.0 contact angle "
        "(61.77 deg, PMC10780492). HONEST LIMIT: the coating solid-surface-energy capstone "
        "(multi-liquid OWK inversion + held-out-liquid prediction) is data-rights-blocked -- "
        "this run's sweep found only single-liquid (water) contact angles in CC-licensed "
        "DGEBA-amine sources, so ADHESION is rights-walled exactly like Tg."),
    "phase0_reconciliation_redteam": pr,
    "owk_adhesion_engine": {
        "theory": eng["theory"],
        "data_source": eng["data_source"],
        "gamma_w_d_consensus": eng["gamma_w_d_consensus"],
        "loo_prediction_kpi": {
            "loo_mae_mN_m": eng["loo_prediction_kpi"]["loo_mae_mN_m"],
            "loo_mape_pct": eng["loo_prediction_kpi"]["loo_mape_pct"],
            "loo_max_abs_err_mN_m": eng["loo_prediction_kpi"]["loo_max_abs_err_mN_m"],
            "n": eng["loo_prediction_kpi"]["n"],
        },
        "positive_control_all_flagged": eng["positive_control_nondispersive"]["all_controls_correctly_flagged"],
        "verdict": eng["verdict"],
    },
    "coating_application": diag["coating_application"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2,
        "independent_runs": True,
        "code_path_independence": "single Python harness, two independent executions (honest scope)",
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": harness_sha,
        "phase0_decision_report_v2_sha256": pr["inputs"]["phase0_decision_report_v2_sha256"],
        "module_manifest_sha256": pr["inputs"]["module_manifest_sha256"],
        "python_version": "3.12",
    },
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-owk-adhesion-phase0+json"
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
