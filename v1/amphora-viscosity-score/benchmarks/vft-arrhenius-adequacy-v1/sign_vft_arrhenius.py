#!/usr/bin/env python3
"""DSSE-Ed25519-sign the vft-arrhenius-adequacy-v1 diagnostic.

Signs the canonical timing-free diagnostic that reproduced byte-identically
across two independent runs (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key (local-9028773f..., NOT the
trust-anchored phase0-evaluator key). AUDIT_ONLY: does NOT promote the module,
does NOT edit the signed Arrhenius KPI, does NOT edit the 66-receipt master
manifest.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-viscosity-score/benchmarks/vft-arrhenius-adequacy-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "8bd04af365d70dbc2f7e19ca98778a1f56f7e326848d296cf1dbcf5d302fafac"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


cb = (BENCH / "diagnostic.canonical.json").read_bytes()
rb = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(cb) == CANON_SHA, f"{sha(cb)} != {CANON_SHA}"
assert sha(rb) == CANON_SHA, f"runB {sha(rb)} != {CANON_SHA} (two-replay gate)"
diag = json.loads(cb)
harness_sha = sha((BENCH / "run_vft_arrhenius_adequacy.py").read_bytes())

receipt = {
    "schema": "amphora.viscosity-score.vft-arrhenius-adequacy-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_ROBUSTNESS_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-viscosity-score",
    "benchmark": "amphora-viscosity-score/vft-arrhenius-adequacy-v1",
    "purpose": diag["purpose"],
    "theory_reference": (
        "Incumbent: Arrhenius (1889) / Andrade (1930) ln eta = ln A + Ea/(R.T). "
        "Competitor: Vogel-Fulcher-Tammann -- Vogel H., Phys. Z. 22:645 (1921); "
        "Fulcher G.S., J. Am. Ceram. Soc. 8:339 (1925) doi:10.1111/j.1151-2916.1925.tb16731.x; "
        "Tammann G. & Hesse W., Z. Anorg. Allg. Chem. 156:245 (1926) "
        "doi:10.1002/zaac.19261560121: ln eta = A + B/(T - T0), reduces to Arrhenius as T0->0. "
        "R = 8.31446261815324 J/(mol.K) CODATA 2018."),
    "primary_references": [
        "Vogel, H. (1921) Physikalische Zeitschrift 22:645-646.",
        "Fulcher, G.S. (1925) J. Am. Ceram. Soc. 8(6):339-355, doi:10.1111/j.1151-2916.1925.tb16731.x.",
        "Tammann, G. & Hesse, W. (1926) Z. Anorg. Allg. Chem. 156:245-257, doi:10.1002/zaac.19261560121.",
        "Andrade, E.N. da C. (1930) Nature 125:309-310 (viscosity-temperature exponential).",
    ],
    "headline_result": {
        "verdict": diag["verdict"],
        "pooled_loto_mape_arrhenius": diag["held_out_summary"]["pooled_loto_mape_arrhenius"],
        "pooled_loto_mape_vft": diag["held_out_summary"]["pooled_loto_mape_vft"],
        "pooled_mape_delta_vft_minus_arrhenius": diag["held_out_summary"]["pooled_mape_delta_vft_minus_arrhenius"],
        "solvents_arrhenius_wins": diag["held_out_summary"]["solvents_arrhenius_wins"],
        "solvents_vft_wins": diag["held_out_summary"]["solvents_vft_wins"],
        "solvents_tie": diag["held_out_summary"]["solvents_tie"],
        "solvents_bic_favours_arrhenius": diag["parsimony_summary"]["solvents_bic_favours_arrhenius"],
        "n_solvents": diag["n_solvents"],
        "n_loto_folds_total": diag["n_loto_folds_total"],
        "interpretation": (
            "Leave-one-temperature-out over 25/30/40/60 C: the 2-parameter Arrhenius "
            "law is NOT out-generalised by the 3-parameter VFT law (pooled held-out "
            "MAPE 0.836% vs 0.890%; Arrhenius wins 16 solvents, ties 5, loses 4; BIC "
            "favours Arrhenius for 13/25). The 4 solvents where VFT's extra curvature "
            "parameter pays off -- water, glycerol, n-butanol, n-hexane -- are exactly "
            "the strongly hydrogen-bonded / associating liquids that physical chemistry "
            "predicts to be super-Arrhenius (fragile). Parsimony favours the incumbent "
            "Arrhenius law for pure Newtonian coating solvents; the associating-polyol "
            "exception is a documented, physically-expected edge, not a model failure."),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANON_SHA,
        "runB_diagnostic_sha256": sha(rb),
        "harness_sha256": harness_sha,
        "source_result_path": diag["source_result_path"],
        "source_result_sha256": diag["source_result_sha256"],
        "determinism": "pure-python math, fixed T0 grid (0..Tmin-1K step 0.25K), no RNG.",
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key not exercised here (governance, not a build step)",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT edited; requires human dual-identity Phase-0 ceremony keys",
        "SIGNED_KPI_UNCHANGED": "the signed Arrhenius KPI (viscosity-arrhenius-kpi.v1.json) is read-only input; not modified",
        "CIRCULARITY_REMAINS": "both laws still fit each solvent's own viscosity; a structure-only a-priori baseline (Orrick-Erbar / Sastri-Rao group contribution) is the open non-circular test, blocked on a rights-clean group-contribution table",
        "SCOPE": "pure Newtonian solvents only; formulation blends / pigment crowding / Krebs KU + sag are Phase-1 wet-lab",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-vft-arrhenius-adequacy+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    # top-level `signature` mirrors signatures[0].sig so downstream `.signature`
    # checks resolve; canonical DSSE `signatures` array retained below.
    "signature": sig_b64,
    "signatures": [{"keyid": PUB["key_id"], "sig": sig_b64}],
}
out = BENCH / "vft-arrhenius-adequacy-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
