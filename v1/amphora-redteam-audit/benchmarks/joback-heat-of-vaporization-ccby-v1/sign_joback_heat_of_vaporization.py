"""DSSE-Ed25519-sign the Joback enthalpy-of-vaporization (dHvap at Tb) audit.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a trust-anchored
phase0 key. AUDIT_ONLY red-team science increment: promotes nothing, signs no phase0
evaluation/review receipt, modifies no existing receipt or the manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/joback-heat-of-vaporization-ccby-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
CANONICAL_SHA = sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "joback_heat_of_vaporization_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.joback-heat-of-vaporization-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "JOBACK_ENTHALPY_OF_VAPORIZATION_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/joback-heat-of-vaporization-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "purpose": (
        "First rights-clean, a-priori validation of an ENTHALPY-OF-VAPORIZATION predictor "
        "(dHvap at the normal boiling point) for the amphora marine two-part epoxy-amine "
        "coating portfolio. dHvap is the single thermodynamic quantity that DRIVES BOTH "
        "solvent-design axes already anchored: VOLATILITY / flash-off (Clausius-Clapeyron "
        "vapour pressure, companion to the Joback boiling-point audit) AND SOLUBILITY / "
        "solvency (cohesive energy E_coh = dHvap - RT, hence Hildebrand/Hansen delta, "
        "companion to the Fedors cohesive-energy audit feeding the crown-jewel amphora-"
        "solvency-score). Nothing in the tree previously predicted dHvap for a NOVEL "
        "solvent or reactive diluent with no measured latent heat; this audit supplies "
        "exactly that, via a THIRD independent group-contribution method that also cross-"
        "checks the cohesive energy the Fedors delta anchor estimates a different way. "
        "Predictor: Joback & Reid 1987 first-order group contribution dHvap(Tb)=15.30 "
        "kJ/mol + sum n_i hvk_i; constants universal and NOT fitted to this panel -> non-"
        "circular. Ground truth: NIST Chemistry WebBook / Majer & Svoboda 1985 critical "
        "experimental dHvap measured AT Tb (public domain), one consistent at-Tb basis. "
        "Every hand-encoded Joback group multiset is formula-checked against RDKit (C,H,O) "
        "so a miscount cannot pass, and the group encoding is byte-identical to the "
        "boiling-point audit for shared solvents. Validated on 18 in-scope coating "
        "solvents (13 core non-associating + 5 alcohols boundary/out); honest domain-of-"
        "applicability study, NOT a Phase-0 gate. Shares the M/rho/Tb/SMILES solvent panel "
        "with the cohesive-energy(delta), refractive-index, surface-tension and boiling-"
        "point audits (cross-audit identity consistency); cyclohexanone from that shared "
        "panel is excluded here to keep the at-Tb truth basis single-source (logged)."),
    "theory": diag["theory"],
    "rights": diag["rights"],
    "n_solvents_total": diag["n_solvents_total"],
    "n_solvents_group_modeled": diag["n_solvents_group_modeled"],
    "excluded_from_shared_panel": diag["excluded_from_shared_panel"],
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
        "+ 4 LOCKED_INTERNAL known-answer; ZERO carry scientific_readiness=VALIDATED; and a "
        "live cross-check of every phase0 promotion policy confirms scientific_success_"
        "required is FALSE in 100% of them (target ceiling LOCKED_INTERNAL, never VALIDATED). "
        "Exactly 1 module (amphora-solvency-score) has EXTERNAL-data validation. 'FULL "
        "Phase-0' is a governance milestone, not validated science. The founder's skepticism "
        "is correct.",
        "does NOT modify any of the 66 signed receipts or the receipts manifest",
        "does NOT claim a coating-BLEND flash-off curve (non-ideal / activity-coefficient; a Phase-1 extension)",
        "does NOT apply any fitted dHvap correction or Watson temperature correction",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key custody only)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-joback-heat-of-vaporization+json"
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
