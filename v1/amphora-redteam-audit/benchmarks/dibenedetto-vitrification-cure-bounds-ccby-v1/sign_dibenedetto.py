"""DSSE-Ed25519-sign the DGEBA/mXDA DiBenedetto vitrification + Flory-Stockmayer
gel physical-bounds consistency audit.

Signs the canonical diagnostic whose bytes reproduced identically across two
independent executions (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-*), explicitly NOT a trust-anchored
phase0 key. AUDIT_ONLY red-team science increment: promotes nothing, signs no
phase0 evaluation/review receipt, modifies no existing receipt or the master
manifest.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/dibenedetto-vitrification-cure-bounds-ccby-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "4cb48c6791484fb993a04f3c648c73e1d0159965675c81fd03e5817957fa8105"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "dibenedetto_vitrification_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.dibenedetto-vitrification-cure-bounds-ccby-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "DIBENEDETTO_VITRIFICATION_FLORY_GEL_CURE_BOUNDS_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/dibenedetto-vitrification-cure-bounds-ccby-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "purpose": (
        "First rights-clean, a-priori, ZERO-FREE-PARAMETER, NON-CIRCULAR physical-bounds "
        "test for isothermal degree-of-cure of a two-part DGEBA + m-xylylenediamine "
        "epoxy-amine network -- the FIRST cured-network (as opposed to solvent-property "
        "or bulk cure-kinetics) axis the portfolio validates against real measured data. "
        "It brackets every measured conversion alpha(T_cure) between the Flory-Stockmayer "
        "GEL floor (structure-only: 1/sqrt((f-1)(g-1)) = 0.577 for DGEBA f=2 + tetrafunctional "
        "diamine g=4) and the DiBenedetto VITRIFICATION ceiling (the alpha at which the "
        "advancing Tg reaches T_cure, computed from three a-priori DGEBA-amine constants "
        "-- Tg0, lambda, matched-material Tg_inf -- fixed from independent literature and "
        "NOT tuned to the panel). Marine relevance: the vitrification ceiling is exactly the "
        "physics that limits achievable cure of a two-part epoxy applied at low ambient "
        "temperature. Truth: measured residual-enthalpy conversion, CC-BY-4.0 "
        "(Nanomaterials 2023, 13(6), 1064; PMC10054629; DOI 10.3390/nano13061064)."
    ),
    "non_circularity": (
        "The predictor consumes ONLY monomer functionalities and three a-priori DGEBA-amine "
        "constants fixed BEFORE analysis and NOT tuned to the conversion data. The measured "
        "alpha(T_cure) column is read ONLY as the validation target. Zero parameters are fit "
        "to the panel; a 3x3 sensitivity sweep over the a-priori box (Tg0 in [-25,-15] C, "
        "lambda in [0.35,0.45]) shows all 7 points stay inside the window (bound is robust, "
        "not a lucky point)."
    ),
    "kpis": diag["kpis"],
    "gates": diag["gates"],
    "verdict": diag["verdict"],
    "honest_limitations": diag["honest_limitations"],
    "red_team_findings_this_run": [
        "UPHELD THE FOUNDER: independently re-parsed all module mission front-matter this "
        "run. 17 modules labelled PHASE_0 = 13 NOT_APPLICABLE + 4 LOCKED_INTERNAL "
        "(known-answer-benchmarks, process-qc-twin, solvency-score, tolerance-robustness) "
        "+ 0 scientific_readiness=VALIDATED; 12 modules are PRE_PHASE_0/UNVALIDATED; "
        "module-manifest lists all modules UNVALIDATED. 'FULL Phase-0' is a GOVERNANCE "
        "milestone, NOT validated science. The founder's skepticism is correct.",
        "TRAP AVOIDED (documented so a future run cannot fall into it): pairing the "
        "NEAT-resin Tg_inf (~111-121 C) with the 8.5 wt% AuNP COMPOSITE alpha(T_cure) "
        "table produces a spuriously tight DiBenedetto point-prediction (MAE~0.03 alpha). "
        "That is a material-mismatch artifact and is REJECTED. Using the matched-material "
        "composite Tg_inf=69.95 C correctly downgrades the claim from 'point predictor' to "
        "'upper-bound consistency', which is the honest result reported here.",
        "This receipt therefore promotes NOTHING and does NOT assert a validated point "
        "predictor; it validates only a necessary-condition physical window.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "code_path_independence": "single Python harness, two independent executions (honest scope)",
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": harness_sha,
    },
    "does_not_close": [
        "does NOT promote amphora-cure-potlife-gate (or any module) to PHASE_0 or change "
        "any scientific_readiness",
        "does NOT add any PHASE_0 module. Live-front-matter reconciliation (verified this "
        "run): 17 modules labelled PHASE_0 = 13 NOT_APPLICABLE + 4 LOCKED_INTERNAL; ZERO "
        "scientific_readiness=VALIDATED. 'FULL Phase-0' is a governance milestone, not "
        "validated science.",
        "does NOT modify any of the 66 signed receipts or the receipts manifest",
        "does NOT claim a validated alpha or Tg point predictor (necessary-condition bound "
        "test only)",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY "
        "key custody only)",
        "does NOT fit any parameter to the validation panel",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-dibenedetto-vitrification-cure-bounds+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
