"""DSSE-Ed25519-sign the Hoftyzer-Van Krevelen a-priori Hansen-VECTOR audit.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), explicitly NOT a trust-anchored
phase0 key. AUDIT_ONLY red-team science increment: promotes nothing, signs no phase0
evaluation/review receipt, modifies no existing receipt or the manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/hvk-hansen-vector-ccby-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
CANONICAL_SHA = sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "hvk_hansen_vector_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.hvk-hansen-vector-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "HVK_HANSEN_VECTOR_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/hvk-hansen-vector-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "purpose": (
        "First rights-clean, a-priori validation of the FULL HANSEN SOLUBILITY VECTOR "
        "(delta_d, delta_p, delta_h) predicted from STRUCTURE ALONE via the Hoftyzer-Van "
        "Krevelen group-contribution method, for the amphora marine two-part epoxy-amine "
        "coating portfolio. The crown-jewel amphora-solvency-score module selects and "
        "blends solvents for the DGEBA-amine binder by placing each solvent in Hansen space "
        "and computing the RED number (Hansen distance to the resin sphere). The prior "
        "Fedors cohesive-energy audit validated only the SCALAR Hildebrand delta (0.9% vs "
        "lit total) and the dispersion component delta_d (3.2% vs lit); it never surfaced "
        "the polar (delta_p) or hydrogen-bonding (delta_h) components, nor the operational "
        "Hansen VECTOR DISTANCE Ra the module actually consumes. A scalar delta cannot tell "
        "an alcohol from an ester of equal delta; only the 3-vector places a solvent for "
        "RED-number selection. This audit closes that gap and EXTENDS the crown jewel to "
        "NOVEL solvents with no measured Hansen parameters. Predictor: Hoftyzer-Van Krevelen "
        "delta_d=SUM(F_di)/V, delta_p=sqrt(SUM(F_pi^2))/V, delta_h=sqrt(SUM(E_hi)/V), V=M/rho "
        "(Van Krevelen 'Properties of Polymers' ch.7; Hansen Handbook 2007); the group "
        "constants are universal literature values NOT re-fit here -> non-circular. Ground "
        "truth: Hansen 2007 Handbook canonical (delta_d,delta_p,delta_h) solvent triples. "
        "Validated on 19 in-scope coating solvents (17 CORE polar/H-bonding/aliphatic + 2 "
        "bare-aromatic/conjugated BOUNDARY). CORE per-component RMSE: delta_d 0.47, delta_p "
        "0.35, delta_h 1.42 MPa^0.5; Hansen vector distance Ra median 1.19, mean 1.45, max "
        "3.71 (o-xylene), all 17/17 within Ra<=5 -- far inside a typical epoxy/DGEBA "
        "interaction radius R0~8-13, so a-priori placement preserves the solvent-selection "
        "decision; 79% lift over a mean-vector null. Operational solvent-selection geometry: "
        "mean solvent-distance rank Spearman 0.87, nearest-replacement-solvent match 15/17. "
        "First-order HvK assigns delta_h=0 to bare aromatic/conjugated rings (no pi-cohesion "
        "group), so benzene/styrene are the declared BOUNDARY, reported not hidden. Honest "
        "domain-of-applicability study, NOT a Phase-0 gate. Shares the SMILES/M/rho panel and "
        "HvK constant table with the Fedors cohesive-energy audit (formula-guarded); a "
        "red-team side-finding of this run corrected an ester-oxygen double-count latent in "
        "that shared decomposition (see receipt.redteam_finding)."),
    "theory": diag["theory"],
    "rights": diag["rights"],
    "n_solvents_total": diag["n_solvents_total"],
    "n_core": diag["n_core"],
    "n_boundary": diag["n_boundary"],
    "redteam_finding": diag["redteam_finding_ester_oxygen_double_count"],
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
        "does NOT promote amphora-solvency-score (or any module) to a new phase or change its scientific_readiness",
        "does NOT add any PHASE_0 module. Live-front-matter reconciliation (verified this "
        "run, embedded above): the modules labelled PHASE_0 are governance NOT_APPLICABLE + "
        "LOCKED_INTERNAL known-answer; ZERO carry scientific_readiness=VALIDATED; and a live "
        "cross-check of every phase0 promotion policy confirms scientific_success_required is "
        "FALSE in 100% of them and ZERO target scientific_readiness=VALIDATED (ceiling "
        "LOCKED_INTERNAL). Exactly 1 module (amphora-solvency-score) has EXTERNAL-data "
        "validation. 'FULL Phase-0' is a governance milestone, not validated science. The "
        "founder's skepticism is correct.",
        "does NOT modify any of the 66 signed receipts or the receipts manifest (the "
        "immutable Fedors receipt with the ester double-count is left untouched; the fix "
        "lives only in this new audit and is logged as a red-team note)",
        "does NOT hardcode an external resin Hansen sphere or claim a specific DGEBA RED-number ranking",
        "does NOT re-fit the Van Krevelen group constants or tune any parameter on the validation panel",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key custody only)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-hvk-hansen-vector+json"
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
