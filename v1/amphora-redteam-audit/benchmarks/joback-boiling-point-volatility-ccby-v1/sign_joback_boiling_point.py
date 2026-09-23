"""DSSE-Ed25519-sign the Joback normal-boiling-point / solvent-volatility audit.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a trust-anchored
phase0 key. AUDIT_ONLY red-team science increment: promotes nothing, signs no phase0
evaluation/review receipt, modifies no existing receipt or the manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/joback-boiling-point-volatility-ccby-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
CANONICAL_SHA = sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "joback_boiling_point_volatility_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.joback-boiling-point-volatility-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "JOBACK_NORMAL_BOILING_POINT_SOLVENT_VOLATILITY_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/joback-boiling-point-volatility-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "purpose": (
        "First rights-clean, a-priori validation of a SOLVENT-VOLATILITY predictor "
        "(normal boiling point Tb + fast/medium/slow evaporation ORDER) for the amphora "
        "marine two-part epoxy-amine coating portfolio. Volatility is one of the two "
        "axes on which a coating solvent/co-solvent package is designed (the other, "
        "solubility, is anchored by the Hildebrand/Hansen delta audit feeding the crown-"
        "jewel amphora-solvency-score). Nothing in the tree previously predicted Tb / "
        "evaporation ordering for a NOVEL solvent or reactive diluent with no measured "
        "boiling point -- this audit supplies exactly that missing companion capability. "
        "Predictor: Joback & Reid 1987 first-order group contribution Tb=198.2K+sum n_i "
        "tbk_i; constants universal and NOT fitted to this panel -> non-circular. Ground "
        "truth: NIST Chemistry WebBook experimental Tb (public domain). Every hand-encoded "
        "Joback group multiset is formula-checked against RDKit (C,H,O) so a miscount "
        "cannot pass. Validated on 19 in-scope coating solvents; honest domain-of-"
        "applicability study, NOT a Phase-0 gate. Shares the M/rho/SMILES solvent panel "
        "with the cohesive-energy(delta), refractive-index and surface-tension audits "
        "(cross-audit identity consistency)."),
    "theory": diag["theory"],
    "rights": diag["rights"],
    "n_solvents_total": diag["n_solvents_total"],
    "n_solvents_group_modeled": diag["n_solvents_group_modeled"],
    "phase0_reconciliation_redteam": diag["phase0_reconciliation_redteam"],
    "kpis": diag["kpis"],
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
        "does NOT promote amphora-molecule-property (or any module) to PHASE_0 or change its scientific_readiness",
        "does NOT add any PHASE_0 module. Live-front-matter reconciliation (verified this "
        "run, embedded above): 17 modules labelled PHASE_0 are 13 governance NOT_APPLICABLE "
        "+ 4 LOCKED_INTERNAL known-answer; ZERO carry scientific_readiness=VALIDATED; exactly "
        "1 (amphora-solvency-score) has EXTERNAL-data validation. 'FULL Phase-0' is a "
        "governance milestone, not validated science. The founder's skepticism is correct.",
        "does NOT modify any of the 66 signed receipts or the receipts manifest",
        "does NOT claim a coating-BLEND flash-off curve (non-ideal / activity-coefficient; a Phase-1 extension)",
        "does NOT apply any fitted Tb correction (that would break non-circularity)",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key custody only)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-joback-boiling-point-volatility+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("canonical_diagnostic_sha256", CANONICAL_SHA)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
