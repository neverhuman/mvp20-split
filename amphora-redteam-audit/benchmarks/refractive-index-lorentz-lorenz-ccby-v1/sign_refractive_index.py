"""DSSE-Ed25519-sign the refractive-index Lorentz-Lorenz audit diagnostic.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a
trust-anchored phase0 key. AUDIT_ONLY red-team science increment: promotes
nothing, signs no phase0 evaluation/review receipt, modifies no existing
receipt or manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/refractive-index-lorentz-lorenz-ccby-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "f35b4532191c0de33104a2cdb32d85e155423664539d960a74dcdf62f70caca9"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "refractive_index_lorentz_lorenz_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.refractive-index-lorentz-lorenz-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "REFRACTIVE_INDEX_LORENTZ_LORENZ_GROUP_CONTRIBUTION_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/refractive-index-lorentz-lorenz-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "purpose": (
        "First rights-clean, a-priori validation of a refractive-index predictor for the "
        "amphora coating portfolio. The Lorentz-Lorenz molar-refraction group-contribution "
        "method (Eisenlohr/Vogel atomic refractions) predicts pure-liquid refractive index "
        "from a pure literature-constant sum (NOT fitted to the validation set -> "
        "non-circular). Refractive index governs coating hiding-power/opacity via the "
        "RI contrast between pigment and cured binder, gloss, and refractometric incoming "
        "QC of resin/solvent identity; R_LL is also the electronic-polarization term of "
        "Clausius-Mossotti, linking RI to film barrier physics. Validated on 20 liquids "
        "spanning the exact chemistries of two-part marine epoxy-amine thinner packages. "
        "Honest domain-of-applicability study; NOT a Phase-0 gate. Complements the "
        "surface-tension Parachor audit (same 20-solvent panel, same M/rho)."),
    "theory": diag["theory"],
    "rights": diag["rights"],
    "n_solvents": diag["n_solvents"],
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
        "does NOT promote amphora-molecule-property (or any module) to PHASE_0",
        "does NOT add any PHASE_0 module. Live-front-matter reconciliation (verified this "
        "run, embedded above): modules labelled PHASE_0 are governance NOT_APPLICABLE + "
        "LOCKED_INTERNAL known-answer; exactly 1 (amphora-solvency-score) has EXTERNAL-data "
        "scientific validation. 'FULL Phase-0' is a governance milestone, not validated science.",
        "does NOT modify any of the 66 signed receipts or the receipts manifest",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing "
        "(AUDIT_ONLY key custody only)",
        "does NOT claim cured-film RI or all-a-priori density (both are Phase-1 extensions)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-refractive-index-lorentz-lorenz+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
