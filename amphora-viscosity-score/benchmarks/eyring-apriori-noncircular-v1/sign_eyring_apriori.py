#!/usr/bin/env python3
"""DSSE-Ed25519-sign the eyring-apriori-noncircular-v1 diagnostic.

Signs the canonical timing-free diagnostic that reproduced byte-identically
across two independent runs (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY Ed25519 key (local-9028773f..., NOT the
trust-anchored phase0-evaluator key) -- the same key as the module's two prior
audit receipts. AUDIT_ONLY: does NOT promote the module, does NOT edit the
signed Arrhenius KPI, does NOT edit the 66-receipt master manifest.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-viscosity-score/benchmarks/eyring-apriori-noncircular-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "852f93f17e34d328467b5ba37f6f2b3e3825bbbf178a7200cf081c871d91fa12"


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
harness_sha = sha((BENCH / "run_eyring_apriori_noncircular.py").read_bytes())

e1 = diag["E1_pre_exponential"]["tier_a_exp_density"]
e2 = diag["E2_activation_energy_ratio"]["tier_a_exp_hvap"]
e3a = diag["E3_zero_parameter_composite"]["TIER_A"]
e3b = diag["E3_zero_parameter_composite"]["TIER_B"]
e4a = diag["E4_transferable_two_constant_loo"]["TIER_A"]
e4b = diag["E4_transferable_two_constant_loo"]["TIER_B"]
e5 = diag["E5_domain_restriction_unassociated_liquids"]

receipt = {
    "schema": "amphora.viscosity-score.eyring-apriori-noncircular-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_THEORY_BASELINE",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-viscosity-score",
    "benchmark": "amphora-viscosity-score/eyring-apriori-noncircular-v1",
    "purpose": diag["purpose"],
    "theory_reference": (
        "Eyring absolute-rate theory of viscous flow: eta(T) = (N_A.h/V_m).exp(dG_vis/(R.T)) "
        "[Eyring 1936, doi:10.1063/1.1749836], with the Glasstone/Laidler/Eyring (1941) "
        "closure dE_vis = dE_vap/2.45 for unassociated liquids, dE_vap = dHvap(Tb) - R.Tb. "
        "Structure-only tier chains Fedors (1974) group-contribution molar volume and "
        "Joback-Reid (1987) group-contribution dHvap, both already signed in-portfolio. "
        "Incumbent comparator: Arrhenius (1889)/Andrade (1930) ln eta = ln A + Ea/(R.T), "
        "2 parameters PER SOLVENT fitted to that solvent's own viscosity. "
        "N_A = 6.02214076e23 /mol and h = 6.62607015e-34 J.s (SI-2019 exact); "
        "R = 8.31446261815324 J/(mol.K) (CODATA 2018)."),
    "primary_references": diag["primary_references"],
    "non_circularity_statement": diag["theory"]["non_circularity"],
    "headline_result": {
        "verdict": diag["verdict"],
        "n_panel_with_molar_volume": diag["panel_construction"]["n_with_molar_volume"],
        "n_structure_only_subpanel": diag["panel_construction"]["n_structure_only_subpanel"],
        "E1_pre_exponential_ratio_geometric_mean": e1["ratio_geometric_mean"],
        "E1_ratio_range": [e1["ratio_min"], e1["ratio_max"]],
        "E1_n_within_factor_2_of_23": e1["n_within_factor_2"],
        "E1_n_within_factor_10_of_23": e1["n_within_factor_10"],
        "E2_classical_denominator": e2["classical_denominator"],
        "E2_empirical_denominator_mean": e2["empirical_denominator_mean"],
        "E2_empirical_denominator_mean_nonassociating":
            e2["empirical_denominator_mean_nonassociating"],
        "E2_ea_mape_vs_fitted": e2["ea_mape_vs_fitted"],
        "E3_zero_param_pooled_mape_tier_a": e3a["pooled_mape_eyring_zero_param"],
        "E3_zero_param_pooled_mape_tier_b": e3b["pooled_mape_eyring_zero_param"],
        "E3_incumbent_insample_mape_ceiling":
            e3a["pooled_mape_incumbent_arrhenius_2param_per_solvent"],
        "E4_tier_b_full_panel_k": e4b["full_panel_k_pre_exponential_multiplier"],
        "E4_tier_b_full_panel_implied_denominator":
            e4b["full_panel_implied_eyring_denominator"],
        "E4_tier_a_pooled_loo_mape": e4a["pooled_loo_mape"],
        "E4_tier_b_pooled_loo_mape": e4b["pooled_loo_mape"],
        "E5_tier_b_nonassociating_loo_mape":
            e5["TIER_B"]["nonassociating"]["E4_pooled_loo_mape"],
        "E5_tier_b_associating_loo_mape":
            e5["TIER_B"]["associating"]["E4_pooled_loo_mape"],
        "E5_pre_exponential_separates_perfectly_at_unity":
            e5["pre_exponential_separation"]["separates_perfectly_at_unity"],
        "interpretation": (
            "Both of Eyring's specific NUMERICAL claims are REFUTED on the coating solvent "
            "panel. The parameter-free pre-exponential A = N_A.h/V_m is wrong by a "
            "geometric-mean factor of 1.87 and spans 0.057-4.97 (only 6/23 within a factor "
            "of 2; 22/23 within a factor of 10, so the classical order-of-magnitude claim "
            "survives and the factor-2 claim does not). The classical energy denominator "
            "2.45 is likewise refuted: the empirical panel mean is 2.89 (3.12 for "
            "unassociated liquids), and imposing 2.45 mispredicts the fitted activation "
            "energy by 27% MAPE. Composed, the ZERO-parameter Eyring prediction reaches "
            "49.2% MAPE (thermodynamic inputs) and 36.6% (fully structure-only) against "
            "the incumbent's 0.28% in-sample ceiling -- but with near-zero systematic bias "
            "(mean log10 bias +0.029 / -0.007) and 10-11 of 13 solvents inside a factor of "
            "2, i.e. unbiased and order-correct rather than merely wrong. Re-fitting "
            "Eyring's FORM with two panel-level constants, scored leave-one-SOLVENT-out, "
            "does not rescue the pooled number (42.3% TIER_B), because the failure is not "
            "calibration but DOMAIN: the four alcohols carry it (84.0% LOO) while the nine "
            "unassociated solvents reach 23.8% LOO from SMILES alone. That is exactly the "
            "restriction Glasstone/Laidler/Eyring themselves place on the law, and it is "
            "independently corroborated by a perfect split of the pre-exponential ratio at "
            "unity (4/4 alcohols below 1.0, 9/9 non-alcohols above). NET: the module gains "
            "its first NON-CIRCULAR viscosity predictor -- SMILES-in, ~24% MAPE, no "
            "viscosity datum for the scored solvent, restricted to non-hydroxyl solvents -- "
            "which is roughly 85x worse than the fitted incumbent and therefore useful ONLY "
            "for screening candidate solvents that have no measured viscosity, never as a "
            "replacement where a measurement exists."),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2,
        "independent_runs": True,
        "canonical_diagnostic_sha256": CANON_SHA,
        "runB_diagnostic_sha256": sha(rb),
        "harness_sha256": harness_sha,
        "inputs": diag["inputs"],
        "determinism": "closed-form OLS, no RNG, no timing, fixed rounding; joins on "
                       "RDKit-canonical SMILES.",
    },
    "rights": diag["rights"],
    "redteam_observation_signed_kpi_ea_not_reproducible":
        diag["redteam_observation_signed_kpi_ea_not_reproducible"],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key not "
                                       "exercised here (governance, not a build step)",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT "
                              "edited; requires human dual-identity Phase-0 ceremony keys",
        "SIGNED_KPI_UNCHANGED": "the signed Arrhenius KPI (viscosity-arrhenius-kpi.v1.json) "
                                "is read-only input; not modified",
        "CIRCULARITY_REMAINS": "CLOSED by this receipt for non-associating pure solvents: a "
                               "SMILES-only predictor consuming zero viscosity information "
                               "about the scored solvent now exists (23.8% LOO MAPE, n=9). "
                               "Still OPEN for associating (hydroxyl-bearing) solvents, "
                               "where the Eyring flow-unit assumption fails (84.0% LOO).",
        "NO_CONFORMAL_INTERVAL": "n=9 in the deployable stratum is too small to claim a "
                                 "calibrated interval; the module's existing conformal "
                                 "receipt covers the FITTED law only, not this a-priori law",
        "WATSON_CORRECTION_ABSENT": "dHvap used at Tb without correction to the 298-333 K "
                                    "window (needs a critical temperature not yet locked); "
                                    "reported activation energies are a lower bound",
        "SCOPE": "pure Newtonian solvents only; formulation blends / pigment crowding / "
                 "Krebs KU + sag are Phase-1 wet-lab",
    },
    "claim_locks": diag["claim_locks"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-eyring-apriori-noncircular+json"
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
out = BENCH / "eyring-apriori-noncircular-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
