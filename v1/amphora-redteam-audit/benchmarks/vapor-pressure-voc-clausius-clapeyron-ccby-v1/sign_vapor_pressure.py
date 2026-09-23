"""DSSE-Ed25519-sign the vapor-pressure P0(25C) / VOC Clausius-Clapeyron+Watson audit.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-*), explicitly NOT a trust-anchored phase0
key. AUDIT_ONLY red-team science increment: promotes nothing, signs no phase0
evaluation/review receipt, modifies no existing receipt or the master manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/vapor-pressure-voc-clausius-clapeyron-ccby-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "5661b63bad11ec46f18fba1a3df43631a08e8eb248a4e967040c9e4e7c3f616b"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "vapor_pressure_voc_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.vapor-pressure-voc-clausius-clapeyron-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "VAPOR_PRESSURE_VOC_CLAUSIUS_CLAPEYRON_WATSON_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/vapor-pressure-voc-clausius-clapeyron-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "purpose": (
        "First rights-clean, a-priori validation of a 25 C saturated vapor pressure "
        "P0(298.15 K) predictor for the amphora coating portfolio -- the quantitative "
        "driver of VOC content / regulatory compliance and of the fast/medium/slow "
        "evaporation balance that sets the application window, sag, solvent-popping and "
        "blush of a two-part epoxy-amine marine coating. Boiling point only ORDERS "
        "solvents and flash point handles safety; neither yields the absolute room-"
        "temperature vapor pressure a VOC calculation needs. This capstone integrates "
        "Clausius-Clapeyron with a Watson-corrected enthalpy of vaporisation down from "
        "the normal boiling point, CONSUMING the two independently-signed anchored axes "
        "(Joback Tb; Joback dHvap at Tb) and a Joback critical temperature cross-checked "
        "vs 8 independent measured Tc. Validated against NIST Chemistry WebBook Antoine "
        "vapor pressures (independent of every model input) at two non-circularity "
        "levels: a PHYSICS path (measured thermochemistry -> isolates the Clausius-"
        "Clapeyron+Watson engine) and a fully structure-only A-PRIORI path. Honest "
        "domain-of-applicability study; NOT a Phase-0 gate."),
    "theory": diag["theory"],
    "rights": diag["rights"],
    "consumes_anchors": diag["consumes_anchors"],
    "n_solvents_total": diag["n_solvents_total"],
    "n_solvents_core": diag["n_solvents_core"],
    "phase0_reconciliation_redteam": diag["phase0_reconciliation_redteam"],
    "kpis": diag["kpis"],
    "gates": diag["gates"],
    "verdict": diag["verdict"],
    "honest_limitations": diag["honest_limitations"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "code_path_independence": "single Python+RDKit harness, two independent executions (honest scope)",
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": harness_sha,
        "rdkit_version": "2026.03.2",
    },
    "does_not_close": [
        "does NOT promote amphora-molecule-property / amphora-sourceability-ehs (or any "
        "module) to PHASE_0 or change any scientific_readiness",
        "does NOT add any PHASE_0 module. Live-front-matter reconciliation (verified this "
        "run, embedded above): 17 modules labelled PHASE_0 = 13 NOT_APPLICABLE + 4 "
        "LOCKED_INTERNAL; ZERO scientific_readiness=VALIDATED; module-manifest lists all "
        "29 modules UNVALIDATED. 'FULL Phase-0' is a governance milestone, not validated science.",
        "does NOT modify any of the 66 signed receipts or the receipts manifest",
        "does NOT claim VOC-compliance certification -- it is a predictive-model audit",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key custody only)",
        "does NOT fit any parameter to the validation panel",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-vapor-pressure-voc-clausius-clapeyron+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
