#!/usr/bin/env python3
"""DSSE-Ed25519-sign the barrier-water-uptake-hydrophilicity-ccby-v1 diagnostic.

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
BENCH = REPO / "amphora-redteam-audit/benchmarks/barrier-water-uptake-hydrophilicity-ccby-v1"
KEY = REPO / ".amphora/control/local-ed25519.key"
PUB = json.loads((REPO / ".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "b927cf73a117efd958a4954f6407b84bc42723334893c479a12585350a1a2c31"


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
harness_sha = sha((BENCH / "barrier_water_uptake_audit.py").read_bytes())

pr = diag["phase0_reconciliation_redteam"]
eng = diag["barrier_water_uptake_engine"]
ins = eng["in_scope_dgeba_amine"]

receipt = {
    "schema": "amphora.redteam-audit.barrier-water-uptake-hydrophilicity-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "BARRIER_WATER_UPTAKE_ENGINE_AND_PHASE0_HONESTY_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/barrier-water-uptake-hydrophilicity-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "target_kpi_id": diag["target_kpi_id"],
    "predecessor": diag["predecessor"],
    "supersedes_nothing": True,
    "purpose": (
        "Two-part AUDIT_ONLY red-team. PART A (founder-facing honesty map, recomputed LIVE "
        "from on-host governance state) directly answers 'do we actually have FULL Phase-0': "
        "NO in the scientific sense -- scientific_readiness==VALIDATED for 0 of 29 modules "
        "(the module-manifest independently lists all 29 as UNVALIDATED); the 10 modules the "
        "report labels PHASE_0 are 7 NOT_APPLICABLE (governance/infra) + 3 LOCKED_INTERNAL; "
        "and scientific_success_required_for_phase0==false in ALL 29 benchmark-locks, so "
        "Phase-0 is a GOVERNANCE gate, not a validated-science gate. This autonomous cron "
        "holding only the LOCAL_DEVELOPMENT_AUDIT_ONLY key cannot and must not promote any "
        "module. PART B is a REAL new-science increment on the #1 marine-coating mission gap: "
        "the BARRIER-WATER axis (equilibrium water uptake of the cured film -- the driver of "
        "osmotic blistering and cathodic disbondment). Against real, rights-clean, "
        "protocol-controlled CC BY 4.0 data (three DGEBA + diamine networks, one immersion "
        "protocol, Polymers 2024 16(1):67 = PMC10780492: EP-CYDM 0.16%%, EP-DDS 1.7%%, "
        "EP-8CH2DA 2.0%%) the natural a-priori hypothesis 'more hydrophilic groups -> more "
        "water' is REFUTED for within-family ranking: two parameter-free hydrophilicity "
        "descriptors (secondary-hydroxyl and total polar-atom concentration) ANTI-correlate "
        "with measured uptake (Spearman -0.50) because the cycloaliphatic CYDM network has "
        "the HIGHEST hydroxyl density yet the LOWEST uptake. The controlling variable within "
        "one resin family is amine-backbone free volume / crosslink density; a free-volume "
        "proxy alone (rho +0.50) captures the extreme but not the polar-sulfone DDS, so with "
        "n=3 and >=2 competing effects the model is underdetermined (no significance claimed "
        "at n=3). A cross-class positive control on canonical polymer physical constants "
        "(rank-only, NO coating claim) shows the same hydrophilicity descriptor DOES rank "
        "uptake across polymer classes spanning >3 orders of magnitude (Spearman 1.00), so "
        "the engine is valid at coarse resolution and it is the within-family, "
        "design-relevant resolution that is model-and-data co-limited. Honest verdict: the "
        "barrier-water-uptake axis cannot be promoted; it needs a validated "
        "free-volume/crosslink descriptor plus protocol-controlled n>=~10 -- the same wall "
        "as network Tg."),
    "phase0_reconciliation_redteam": {
        "inputs": pr["inputs"],
        "live_counts": pr["live_counts"],
        "n_modules_scientifically_VALIDATED": pr["n_modules_scientifically_VALIDATED"],
        "scientific_readiness_all_modules_decision_report": pr["scientific_readiness_all_modules_decision_report"],
        "scientific_readiness_all_modules_module_manifest": pr["scientific_readiness_all_modules_module_manifest"],
        "benchmark_lock_governance": pr["benchmark_lock_governance"],
        "founder_answer_do_we_have_full_phase0": pr["founder_answer_do_we_have_full_phase0"],
    },
    "barrier_water_uptake_engine": {
        "theory": eng["theory"],
        "in_scope_data_source": ins["data_source"],
        "in_scope_n_systems": ins["n_systems"],
        "in_scope_measured_uptake_order": ins["measured_uptake_order_low_to_high"],
        "in_scope_spearman_vs_measured_uptake": ins["spearman_vs_measured_uptake"],
        "in_scope_validation_bar_spearman": ins["validation_bar_spearman"],
        "in_scope_hydrophilicity_group_density_REFUTED": ins["hydrophilicity_group_density_REFUTED_within_family"],
        "cross_class_spearman_delta_h_vs_uptake": eng["cross_class_positive_control"]["spearman_delta_h_vs_uptake"],
        "cross_class_engine_valid": eng["cross_class_positive_control"]["engine_valid_cross_class"],
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
ptype = "application/vnd.amphora.redteam-barrier-water-uptake-phase0+json"
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
