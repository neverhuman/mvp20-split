"""DSSE-Ed25519-sign the Catoire-Naudet closed-cup flash-point / GHS-category audit.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a trust-anchored
phase0 key. AUDIT_ONLY red-team science increment: promotes nothing, signs no phase0
evaluation/review receipt, modifies no existing receipt or the manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/catoire-flash-point-ghs-ccby-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
CANONICAL_SHA = sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "catoire_flash_point_ghs_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.catoire-flash-point-ghs-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "CATOIRE_FLASH_POINT_GHS_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/catoire-flash-point-ghs-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "purpose": (
        "First rights-clean, a-priori validation of a CLOSED-CUP FLASH POINT and GHS "
        "flammable-liquid CATEGORY predictor for the amphora marine two-part epoxy-amine "
        "coating portfolio. The flash point is the single most consequential safety / "
        "regulatory number on a coating's solvent package: it sets the GHS label category, "
        "the IMDG / ADR dangerous-goods class for shipping the paint, and on-site storage / "
        "hot-work controls, and is the primary flammability gate for the sourceability / EHS "
        "lane. The tree already anchors the two thermodynamic DRIVERS of the flash point -- "
        "the normal boiling point (Joback boiling-point audit) and the enthalpy of "
        "vaporization (Joback dHvap audit) -- but nothing previously turned those into the "
        "flash point / GHS category a formulator and a shipping desk act on. This audit is "
        "the CAPSTONE closing that loop. Predictor: Catoire & Naudet 2004 unique flash-point "
        "equation FP = 1.477*Tb^0.79686*dHvap298^0.16845*nC^(-0.05948); the four constants "
        "were regressed on a SEPARATE 59-compound set and are NOT re-fit here -> non-circular. "
        "Ground truth: independent experimental closed-cup flash points (GESTIS/CRC/PubChem/EC "
        "regulatory). Validated on 18 in-scope coating solvents (13 core non-associating + 5 "
        "alcohol boundary). Core Track A (experimental Tb+dHvap298 inputs): MAE 2.34 K -- at "
        "Catoire's own reported ~2.9 K accuracy -- all 13/13 within +-5 K, Spearman(FP order) "
        "0.989, 84% lift over a mean-FP null, and 11/13 exact GHS category (both misses sit "
        "within ~2 K of the 23 C Cat2/Cat3 line, inside the literature FP scatter). Alcohols "
        "MAE 1.24 K (Catoire captures H-bonding via dHvap). Track B replaces Tb with its "
        "Joback structure-only prediction (novel-molecule path): MAE 3.97 K. Honest domain-"
        "of-applicability study, NOT a Phase-0 gate. Shares the Tb/SMILES/Joback-group panel "
        "with the boiling-point and dHvap audits (formula-guarded, byte-identical multisets); "
        "self-consistency triangulation: feeding independent experimental Tb & dHvap298 and "
        "recovering the independent experimental FP cross-validates the thermodynamic inputs."),
    "theory": diag["theory"],
    "rights": diag["rights"],
    "n_solvents_total": diag["n_solvents_total"],
    "n_core": diag["n_core"],
    "n_boundary": diag["n_boundary"],
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
        "required is FALSE in 100% of them and ZERO target scientific_readiness=VALIDATED "
        "(ceiling LOCKED_INTERNAL). Exactly 1 module (amphora-solvency-score) has EXTERNAL-"
        "data validation. 'FULL Phase-0' is a governance milestone, not validated science. "
        "The founder's skepticism is correct.",
        "does NOT modify any of the 66 signed receipts or the receipts manifest",
        "does NOT claim a solvent-BLEND flash point (non-ideal / activity-coefficient; a Phase-1 extension)",
        "does NOT re-fit the Catoire constants or tune any parameter on the validation panel",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key custody only)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-catoire-flash-point-ghs+json"
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
