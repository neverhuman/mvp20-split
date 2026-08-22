#!/usr/bin/env python3
"""DSSE-Ed25519-sign the conformal-interval-v1 diagnostic (amphora-viscosity-score).

Signs the canonical timing-free diagnostic that reproduced byte-identically across
two independent runs (two-replay SHA gate = PASS), with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key (local-9028773f..., NOT the trust-anchored
phase0-evaluator key). AUDIT_ONLY: does NOT promote the module, does NOT edit the
signed Arrhenius KPI, does NOT edit the 66-receipt master manifest.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-viscosity-score/benchmarks/conformal-interval-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "5f89efb3ba40870de5bd06d47df62453c7cdcf1085790d953e236ee05dfa24c6"


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
harness_sha = sha((BENCH / "run_viscosity_conformal_interval.py").read_bytes())

arr = diag["arrhenius"]
a10 = arr["per_alpha"]["0.10"]
a05 = arr["per_alpha"]["0.05"]
a20 = arr["per_alpha"]["0.20"]

receipt = {
    "schema": "amphora.viscosity-score.conformal-interval-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_ROBUSTNESS_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-viscosity-score",
    "benchmark": "amphora-viscosity-score/conformal-interval-v1",
    "purpose": diag["purpose"],
    "theory_reference": (
        "Distribution-free split / jackknife-LOO conformal prediction wrapped around "
        "the incumbent 2-parameter Arrhenius (1889) / Andrade (1930) viscosity-"
        "temperature extrapolator ln eta = ln A + Ea/(R.T). Conformity score = "
        "abs(ln eta_pred - ln eta_true) at held-out 30 C. Marginal finite-sample "
        "coverage guarantee per Vovk-Gammerman-Shafer (2005) / Papadopoulos (2002); "
        "family-conditional (Mondrian) validity per Vovk (2012); deployment-band "
        "uncertainty via seeded percentile bootstrap (Efron 1979). "
        "R = 8.31446261815324 J/(mol.K) CODATA 2018."),
    "primary_references": [
        "Vovk, V., Gammerman, A., Shafer, G. (2005) Algorithmic Learning in a Random World, Springer, ISBN 978-0-387-00152-4.",
        "Papadopoulos, H. et al. (2002) Inductive confidence machines for regression, ECML 2002, LNCS 2430:345-356, doi:10.1007/3-540-36755-1_29.",
        "Barber, R.F., Candes, E.J., Ramdas, A., Tibshirani, R.J. (2021) Predictive inference with the jackknife+, Ann. Statist. 49(1):486-507, doi:10.1214/20-AOS1965.",
        "Vovk, V. (2012) Conditional validity of inductive conformal predictors, ACML 2012, PMLR 25:475-490.",
        "Efron, B. (1979) Bootstrap methods: another look at the jackknife, Ann. Statist. 7(1):1-26, doi:10.1214/aos/1176344552.",
    ],
    "headline_result": {
        "verdict": diag["verdict"],
        "n_solvents": diag["n_solvents"],
        "marginal_loo_coverage_vs_nominal": {
            "alpha_0.20": {"nominal": a20["nominal_coverage"], "loo": a20["loo_marginal_coverage"]},
            "alpha_0.10": {"nominal": a10["nominal_coverage"], "loo": a10["loo_marginal_coverage"]},
            "alpha_0.05": {"nominal": a05["nominal_coverage"], "loo": a05["loo_marginal_coverage"]},
        },
        "deploy_band_mult_factor_90pct": a10["deploy_band_mult_factor"],
        "deploy_band_mult_factor_95pct": a05["deploy_band_mult_factor"],
        "families_undercovering_at_90pct": a10["families_undercovering"],
        "worst_residual_solvent": arr["score_stats_ln"]["argmax_solvent"],
        "arrhenius_tighter_than_vft_all_alphas": all(
            v["tighter_model"] == "arrhenius" for v in diag["arrhenius_vs_vft_band"].values()),
        "interpretation": (
            "Wrapping the signed Arrhenius viscosity-temperature KPI in a "
            "distribution-free conformal predictor over the 25 rights-clean pure "
            "Newtonian solvents yields MARGINAL coverage that matches nominal "
            "(0.80 / 0.92 / 0.96 observed at nominal 0.80 / 0.90 / 0.95) with an "
            "exceptionally tight deployment band -- a multiplicative viscosity "
            "factor of only ~1.0076 at 90% (+-0.76%), because held-out 30 C is an "
            "INTERPOLATION inside the 25-60 C training range where the Arrhenius law "
            "is near-exact. BUT the marginal guarantee HIDES a family-conditional "
            "gap: the alcohol family (methanol/ethanol/n-butanol/isopropanol) "
            "under-covers (0.75 at 90% nominal), with isopropanol the single worst "
            "extrapolation residual (0.008 ln = 0.8%) -- consistent with the known "
            "super-Arrhenius / hydrogen-bonded behaviour of associating liquids and "
            "mirroring the family-conditional coverage gap already documented for "
            "cure-potlife. The Arrhenius conformal band is tighter than the "
            "3-parameter VFT band at every alpha, so parsimony pays off in interval "
            "WIDTH as well as point accuracy. Practical rule: the incumbent "
            "Arrhenius interpolation carries a trustworthy +-1% marginal band, but "
            "alcohols warrant a family-conditional (Mondrian) widening before "
            "decision use."),
    },
    "fail_closed_probes": diag["fail_closed"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "canonical_diagnostic_sha256": CANON_SHA,
        "runB_diagnostic_sha256": sha(rb),
        "harness_sha256": harness_sha,
        "source_result_path": diag["source_result_path"],
        "source_result_sha256": diag["source_result_sha256"],
        "determinism": ("pure-python math + exact integer order-statistic conformal "
                        "quantile (no float-quantile interpolation) + seeded bootstrap "
                        "random.Random(20260728); no external data fetched."),
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key not exercised here (governance, not a build step)",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT edited; requires human dual-identity Phase-0 ceremony keys",
        "SIGNED_KPI_UNCHANGED": "the signed Arrhenius KPI (viscosity-arrhenius-kpi.v1.json) is read-only input; not modified",
        "FAMILY_CONDITIONAL_OPEN": "Mondrian per-family conformal is under-powered (alcohol n=4, most classes n<=3); a rights-clean multi-temperature solvent set with >=10 per chemical family is the Phase-1 need to certify per-family bands",
        "CIRCULARITY_REMAINS": "still a per-solvent temperature fit; a structure-only a-priori baseline (Orrick-Erbar / Sastri-Rao group contribution) remains the open non-circular test, blocked on a rights-clean group-contribution table",
        "SCOPE": "pure Newtonian solvents only; formulation blends / pigment crowding / Krebs KU + sag are Phase-1 wet-lab",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-conformal-interval+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signature": sig_b64,
    "signatures": [{"keyid": PUB["key_id"], "sig": sig_b64}],
}
out = BENCH / "conformal-interval-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
# verify signature round-trips
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
pk.verify(base64.standard_b64decode(sig_b64), pae(ptype, body))
print("SIGNATURE_VERIFY OK")
