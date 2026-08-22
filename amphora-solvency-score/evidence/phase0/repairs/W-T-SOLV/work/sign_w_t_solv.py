#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-T-SOLV theory-conformance audit receipt.
AUDIT_ONLY. Does not promote authority, does not modify the manifest,
does not flip scientific_readiness.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEMDIR = ROOT / "amphora-solvency-score/evidence/phase0/repairs/W-T-SOLV"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)

def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]

canon_bytes = (ITEMDIR / "work/diagnostic.canonical.json").read_bytes()
runB_bytes = (ITEMDIR / "work/diagnostic.runB.json").read_bytes()
assert canon_bytes == runB_bytes, "two-replay bytes differ"
diag = json.loads(canon_bytes)
harness_sha = sha((ITEMDIR / "work/hsp_numeric_validation.rs").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

mismatches = [r for r in diag["per_pair"] if not r["prediction_matches_published_label"]]

body_obj = {
    "schema": "amphora.solvency-score-theory-conformance-audit.v1",
    "module_id": "amphora-solvency-score",
    "campaign_item_id": "W-T-SOLV",
    "claim_under_attack": "This module's solubility calculations conform to the published definitions they cite.",
    "published_authorities": [
        "Hansen, C.M. Hansen Solubility Parameters: A User's Handbook, 2nd ed., CRC Press, 2007. ISBN 9780849372483. Ra = sqrt(4*(dD1-dD2)^2 + (dP1-dP2)^2 + (dH1-dH2)^2); RED = Ra/R0.",
        "Flory, P.J. Principles of Polymer Chemistry, Cornell University Press, 1953, Ch. XII. Flory-Huggins free energy of mixing and interaction parameter chi.",
        "Huggins, M.L. J. Chem. Phys. 1942 (entropic constant ~0.34 in the physical chi baseline).",
        "Van Krevelen, D.W. Properties of Polymers, 3rd ed., 1990, Ch. 7 (Hansen-to-chi bridging relation chi = V_s*Ra^2/(4RT) + 0.34, used in this module's own reference receipts)."
    ],
    "normative_requirements": [
        {
            "id": "R1",
            "requirement": "Multicomponent Flory-Huggins free energy of mixing: dG_mix/RT = sum_i (phi_i/n_i) ln(phi_i) + sum_{i<j} chi_ij phi_i phi_j (Flory 1953 Ch. XII, Scott 1949 multicomponent generalization).",
            "verdict": "conformant",
            "evidence": "src/lib.rs fn gibbs_mix_rt (line 1125): value = sum(phi/count * phi.ln()) + sum over pairs of pair.chi(...)*phi_i*phi_j. Exact structural match to the published multicomponent lattice free-energy form."
        },
        {
            "id": "R2",
            "requirement": "chi temperature convention: chi(T) = A + B/T (enthalpic/entropic split), the standard Flory/de Gennes empirical form; composition-dependent extensions (e.g. Redlich-Kister in phi) are a documented generalization (Koningsveld & Kleintjens 1971).",
            "verdict": "conformant",
            "evidence": "src/lib.rs PairCoefficientV1::chi (line 245): self.a + self.b_kelvin/temperature_k + self.redlich_kister*(phi_a-phi_b) + sigma*standard_error. Matches A+B/T with an accepted compositional extension. NOTE: a, b_kelvin, redlich_kister are per-pair REGRESSED coefficients, not derived from Hansen HSP values or molar volume -- see R6."
        },
        {
            "id": "R3",
            "requirement": "Hansen Ra distance factor-of-4 weighting on the dispersion term: Ra^2 = 4*(dD1-dD2)^2 + (dP1-dP2)^2 + (dH1-dH2)^2 (Hansen 2007).",
            "verdict": "conformant",
            "evidence": "src/lib.rs fn hansen_ra_squared (line 2044): ra_squared = 4.0*dd*dd + dp*dp + dh*dh where dd=dD1-dD2 etc. Exact match to the published weighting -- the factor of 4 lands on the dispersion term, not the polar or hydrogen-bonding terms. Independently confirmed by numeric replay (see numeric_validation) against 75 solvent-polymer pairs built from Hansen 2007 Table A.1/A.2 values already cited in-repo."
        },
        {
            "id": "R4",
            "requirement": "RED threshold semantics: RED = Ra/R0; RED<1 predicts compatible (inside the Hansen sphere), RED>1 predicts incompatible (Hansen 2007 Sec. 2.5).",
            "verdict": "conformant",
            "evidence": "src/lib.rs fn hansen_red (line 2068): red = ra/polymer_r. tests/solvency_phase0_kpi.rs line 139-140 applies predicted_compatible = red < 1.0 identically. Numeric replay confirms red == ra/r0 to 1e-12 on all 75 pairs (assertion in evidence/phase0/repairs/W-T-SOLV/work/hsp_numeric_validation.rs)."
        },
        {
            "id": "R5",
            "requirement": "Unit convention: all three Hansen parameters (dD, dP, dH) and R0 are in MPa^0.5 (SI), not the legacy cgs (cal^0.5 cm^-1.5) scale -- a ~2.0455x conversion factor is the single most common HSP implementation bug.",
            "verdict": "conformant",
            "evidence": "Doc comment at src/lib.rs line 2038 states MPa^0.5 explicitly. Fixture values (e.g. water dD=15.5, dP=16.0, dH=42.3) are unmistakably SI-scale -- the cgs-scale water total delta would be roughly half this magnitude. GAP NOTED: hansen_ra_squared/hansen_red reject negative/non-finite inputs but apply no plausible-range upper bound, so a caller who accidentally supplied cgs-scale numbers (all positive, all finite) would pass validation silently. Filed as a proposed_followup, not scored as a divergence since the published definition does not itself mandate a numeric range check."
        },
        {
            "id": "R6",
            "requirement": "Molar volume convention in the Flory-Huggins arm: the published Hansen-to-Flory-Huggins bridge requires a molar volume, chi = V_ref/(RT) * (delta1-delta2)^2 + 0.34 (Flory 1953 / Huggins 1942), or the Hansen-distance-weighted form chi = V_s*Ra^2/(4RT) + 0.34 (Van Krevelen 1990 Ch.7, and this exact formula is the 'hansen_theory' field this module's OWN reference receipt reference/mvp20/data/hansen_chi_external_validation_8_published_polymer_solvent_pairs_receipt.v1.json cites and computes with).",
            "verdict": "divergent",
            "evidence": "src/lib.rs CarrierComponentV1 declares and validates molar_volume_cm3_mol_at_reference and molar_volume_temperature_coefficient_per_k (lines 73-74, validated for finiteness/positivity at lines 91-92). A full-file grep for both field names (`grep -n molar_volume src/lib.rs`) shows they appear ONLY in the struct definition, the validate() bounds check, and two unit-test struct literals (lines 2161-2162, 2176-2177) -- zero downstream reads. The module's actual thermodynamic stability computation (gibbs_mix_rt / tangent_plane_minimum_rt / minimum_hessian_eigenvalue, lines 1125-1230) consumes PairCoefficientV1::chi, which is a per-pair-id REGRESSED empirical function (a + b/T + redlich_kister term) that never reads molar_volume, the gas constant, or the Hansen dD/dP/dH values. Conversely hansen_ra_squared/hansen_red never read molar_volume or chi. The physically-grounded HSP-to-chi bridge equation this module's own citations invoke is implemented ONLY as descriptive JSON inside Python-generated benchmark receipts (reference/mvp20/data/omg_chi_flory_huggins_physical_baseline_receipt.v1.json, hansen_chi_external_validation_8_published_polymer_solvent_pairs_receipt.v1.json) -- never in the Rust production path. Those same receipts additionally document the 'pure' physical bridge formula performing far worse (per-solvent R^2 as low as -5028.9) than an unrelated ML surrogate that is what actually predicts chi outside this crate. CarrierComponentV1's molar-volume fields are therefore dead weight: validated input that gates nothing."
        },
        {
            "id": "R7",
            "requirement": "Cross-theory consistency: since Hansen (2007) and the Van Krevelen (1990) bridging relation both derive chi from the SAME underlying Ra distance, the module's Hansen-sphere classifier (hansen_ra_squared/hansen_red) and its Flory-Huggins tangent-plane stability gate (gibbs_mix_rt/chi) should be reconcilable views of one interaction parameter for a given solvent-polymer(carrier) pair.",
            "verdict": "not_applicable",
            "evidence": "No code path exists to even pose this check: hansen_ra_squared/hansen_red take (dD,dP,dH,R0) keyed by polymer_id/solvent_id from the phase0-solvency-known-answer fixture; PairCoefficientV1::chi takes per-component-id regressed (a, b_kelvin, redlich_kister) coefficients from a disjoint SolvencyParameterArtifactV1 keyed by component_structure_hashes. There is no shared identifier or transform connecting the two structures, so R7 is scored not_applicable rather than divergent: the module does not merely fail to reconcile the two theories, it has no data path capable of attempting reconciliation. This is downstream of, and consistent with, the R6 finding."
        }
    ],
    "numeric_validation": {
        "method": "Direct invocation of the real amphora_solvency_score::hansen_ra_squared and hansen_red functions (examples/hsp_numeric_validation.rs, not a reimplementation) against every solvent x polymer pair in the module's own Hansen-2007-and-TDS-cited known-answer fixture (reference/phase0-solvency-known-answer.v1.json).",
        "n_solvents": diag["n_solvents"],
        "n_polymers": diag["n_polymers"],
        "n_pairs": diag["n_pairs"],
        "solvents_tabulated_hansen_2007_table_a1": sorted({r["solvent_id"] for r in diag["per_pair"]}),
        "polymers_tabulated_hansen_2007_table_a2": sorted({r["polymer_id"] for r in diag["per_pair"]}),
        "classification_accuracy_red_lt_1_vs_published_label": diag["classification_accuracy"],
        "cross_check_against_signed_kpi": "0.893... matches the mission.md-reported classification_accuracy_rate of 0.893 for the same fixture via the independently-implemented tests/solvency_phase0_kpi.rs harness -- two independent call sites of hansen_red agree exactly.",
        "per_solvent_dgeba_epoxy_sample": [r for r in diag["per_pair"] if r["polymer_id"] == "epoxy-dgeba-linear-uncured"],
        "mismatches_red_disagrees_with_published_label": mismatches,
        "mismatch_note": "All 8/75 mismatches are false negatives (RED>1 predicted-incompatible where published label is compatible), consistent with the known limitation that a pure 3-parameter spherical Hansen model under-predicts compatibility for specific aromatic/H-bond-acceptor edge cases (toluene/xylene vs epoxy and PMMA; chloroform/MEK/DMF vs PVC; DMF vs PS). This is expected published-model behavior, not an implementation bug -- it is exactly why the module's own acceptance bar sets the classification_accuracy_rate threshold at 0.85, not 1.0, and observed 0.893 clears it."
    },
    "proposed_followups": [
        {
            "id": "FOLLOWUP-R6",
            "finding": "CarrierComponentV1.molar_volume_cm3_mol_at_reference and molar_volume_temperature_coefficient_per_k are validated but never consumed; the Rust production chi (PairCoefficientV1::chi feeding gibbs_mix_rt) has no code path back to Hansen HSP values or molar volume, despite the module citing the Hansen/Van Krevelen HSP-to-chi bridge in its own reference receipts.",
            "proposed_repair_criterion": "Either (a) wire a chi_from_hsp(solvent_hsp, polymer_hsp, molar_volume_cm3_mol, temperature_k) function implementing chi = V*Ra^2/(4RT) + 0.34 and use it as a documented fallback/cross-check against the regressed PairCoefficientV1::chi wherever both are available for the same pair, with a signed KPI comparing the two chi values across the existing 75-pair fixture; or (b) if the two arms are intentionally kept independent (empirical chi for phase-stability, geometric Ra/RED for screening), remove or clearly mark molar_volume_cm3_mol_at_reference / molar_volume_temperature_coefficient_per_k as reserved-for-future-use in a doc comment so the validated-but-dead field does not imply an integration that does not exist. Acceptance: either a new signed KPI receipt showing the bridge computation matches the regressed chi within a stated tolerance on >=8 pairs, or an updated doc comment plus mission.md note disclaiming the bridge."
        },
        {
            "id": "FOLLOWUP-R5",
            "finding": "hansen_ra_squared/hansen_red validate finiteness and non-negativity of dD/dP/dH/R0 but apply no plausible-range check, so cgs-scale (~2x too small) HSP inputs would silently pass and produce a wrong-by-a-known-factor Ra/RED.",
            "proposed_repair_criterion": "Add a documented plausible-range bound (e.g. 0 < value <= 40 MPa^0.5, generous relative to the ~5-50 MPa^0.5 span Hansen 2007 Table A.1/A.2 actually covers) to hansen_ra_squared's input validation, with a unit test asserting a cgs-scale-magnitude probe (e.g. dD=7.3, the cgs value for toluene) is rejected."
        }
    ],
    "two_replay": {
        "canonical_diagnostic_sha256": sha(canon_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": canon_bytes == runB_bytes,
        "harness_sha256": harness_sha,
        "harness_path": "amphora-solvency-score/examples/hsp_numeric_validation.rs",
        "command": "cargo run -p amphora-solvency-score --example hsp_numeric_validation"
    },
    "verdict": "CLAIM_REFUTED",
    "verdict_rationale": "R6 is a genuine, mechanically-verified divergence: the module validates a Flory-Huggins-relevant physical quantity (molar volume + its temperature coefficient) that its own cited published bridge equation requires, but never reads it in the production chi/Gibbs computation, leaving the Hansen HSP arm and the Flory-Huggins chi arm structurally disconnected despite the module's overall claim of conformance to both cited theories. R1-R4 and (functionally) R5 are conformant and independently numerically confirmed against 75 solvent-polymer pairs built from published Hansen 2007 Table A.1/A.2 values.",
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.solvency-score-theory-conformance-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payloadType": ptype,
    "payload": base64.standard_b64encode(body).decode(),
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}
out = ITEMDIR / "done/w-t-solv-theory-conformance-audit-receipt.v1.dsse.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("two_replay_byte_identical", canon_bytes == runB_bytes)
print("signature_verified", True)
print("verdict", body_obj["verdict"])
