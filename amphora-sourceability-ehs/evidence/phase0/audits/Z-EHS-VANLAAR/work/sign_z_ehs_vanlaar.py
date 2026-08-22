#!/usr/bin/env python3
"""Signs the Z-EHS-VANLAAR done receipt: independent non-ideality (van Laar,
1910, from a published azeotrope) audit of the mixture-additivity-raoult-osha
ideal-solution dominance/crossover claim for the methanol wash-carryover
blends. AUDIT_ONLY. Does not modify the attacked KPI/receipt, does not touch
mission.md front-matter, does not touch the manifest, does not change any
procurement_gate_outcome -- disclosure only, same conservative-default
posture established by W-EHS1/EHS-HCOMP.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
ITEM_DIR = MOD / "evidence/phase0/audits/Z-EHS-VANLAAR"
WORK = ITEM_DIR / "work"

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())

OUT_PATH = MOD / "reference/mvp20/data/mixture_additivity_nonideality_vanlaar_audit_receipt.v1.json"

THIS_FIRE_ID = "20260816T060001-3435018-8c4b61ae524f"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def load_seed(p: Path) -> bytes:
    b = p.read_bytes().strip()
    if len(b) == 64:
        try:
            return bytes.fromhex(b.decode())
        except Exception:
            pass
    return b[:32]


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
tbr = {k.get("role"): k for k in TRUST["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

diag_a_bytes = (WORK / "diagnostic.canonical.json").read_bytes()
diag_b_bytes = (WORK / "diagnostic.runB.json").read_bytes()
diag_a = json.loads(diag_a_bytes)
two_replay_byte_identical = sha(diag_a_bytes) == sha(diag_b_bytes)
assert two_replay_byte_identical, "two-replay byte-stability gate FAILED"
assert diag_a["any_dominance_flip_under_van_laar_methanol_gamma"] is True

kpi_bytes = (MOD / "evidence/phase0/kpis/mixture-additivity-raoult-osha-inhalation-prescreen-kpi.v1.json").read_bytes()
receipt_bytes = (MOD / "reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json").read_bytes()

flips_summary = []
for bid, b in diag_a["blends"].items():
    for t in ("15.0", "25.0", "40.0"):
        pt = b["per_temperature"][t]
        if pt["dominance_flips_under_real_gamma"]:
            flips_summary.append({
                "blend_id": bid, "T_C": float(t),
                "dominant_contributor_claimed_ideal_gamma1": pt["dominant_contributor_ideal_gamma1"],
                "dominant_contributor_under_published_van_laar_gamma": pt["dominant_contributor_with_real_gamma"],
                "gamma_crit_the_claim_itself_reports": pt["gamma_crit_methanol_to_overtake_dominant_per_module_definition"],
                "gamma_methanol_from_published_azeotrope_van_laar_fit": pt["gamma_methanol_van_laar_at_this_x_and_T"],
            })

body_obj = {
    "schema": "amphora.sourceability-ehs.audit.z-ehs-vanlaar.v1",
    "audit_item_id": "Z-EHS-VANLAAR",
    "module": "amphora-sourceability-ehs",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_existing_receipts_or_kpis": False,
    "modifies_procurement_gate_outcome": False,
    "fire_id": THIS_FIRE_ID,
    "date": "2026-08-16",
    "claim_under_attack": {
        "kpi_path": "amphora-sourceability-ehs/evidence/phase0/kpis/mixture-additivity-raoult-osha-inhalation-prescreen-kpi.v1.json",
        "kpi_sha256": sha(kpi_bytes),
        "scientific_receipt_path": "amphora-sourceability-ehs/reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json",
        "scientific_receipt_sha256": sha(receipt_bytes),
        "field": "blends[wash_carryover_methanol_1pct, wash_carryover_methanol_3pct].dominant_contributor "
                 "and observed_kpi_summary.crossover_predicted_mass_fraction_25C / crossover_prediction_bracketed_at_all_T",
        "claim_text": (
            "Under Raoult's law with gamma_i=1 (ideal solution, declared assumption), m_xylene is the "
            "dominant MHI_sat contributor (not methanol, the pure-component worst actor) in the "
            "wash_carryover_methanol_1pct and wash_carryover_methanol_3pct blends at every T in 15-40C; "
            "the closed-form dominance-crossover mass fraction is 3.7171 wt% methanol at 25C and this "
            "value is 'bracketed at all T' by the 1/3/6 wt% carryover series (i.e. crossover sits strictly "
            "between the 3pct and 6pct blends). The receipt itself reports a gamma_crit sensitivity metric "
            "(the activity coefficient a non-dominant constituent needs to overtake the dominant one) and "
            "explicitly declares 'alcohol + aromatic blends show positive deviation (gamma_alcohol > 1)' "
            "without quantifying it: 'We do NOT invent activity coefficients... gamma_crit... states "
            "exactly how much non-ideality the dominance call can absorb.'"
        ),
        "why_this_is_the_strongest_untested_standing_claim": (
            "Every prior EHS falsification fire attacked the single-substance VHR/GHS/OSHA-attribution "
            "receipts (temperature envelope, PubChem CID/H-statement provenance, Table Z-1/Z-2 attribution). "
            "This KPI's central quantitative finding -- that a trace methanol carryover overtakes the bulk "
            "aromatic solvent above a few weight percent -- had never been checked against real "
            "(non-ideal) physics, despite the receipt itself flagging gamma_crit as exactly the number "
            "such a check should compare against. It carries a real, sourceable published activity "
            "coefficient (methanol in aromatic hydrocarbons is famously non-ideal -- it is why "
            "methanol-toluene forms a minimum-boiling azeotrope at all), unlike the module's other "
            "single-substance claims which have already been through several rounds of provenance audits."
        ),
    },
    "refutation_criterion": (
        "For at least one admitted wash_carryover_methanol_{1,3}pct blend at at least one T in the "
        "module's own 15-40C envelope: if a REAL, independently-sourced (published, not fabricated, not "
        "fitted to this module's own outputs) activity coefficient for methanol in an aromatic-hydrocarbon "
        "solvent, evaluated at that blend's actual methanol mole fraction, EXCEEDS the receipt's own "
        "reported gamma_crit_to_overtake_dominant for methanol in that blend/T, then the receipt's stated "
        "dominant_contributor (m_xylene) for that blend/T is refuted -- real physics says methanol "
        "dominates, not the bulk aromatic, and the closed-form crossover mass fraction is refuted as an "
        "underestimate of how little methanol carryover is needed to govern the blend's inhalation hazard."
    ),
    "method": {
        "activity_coefficient_source": "van Laar (1910) two-parameter model, closed-form-inverted from a "
            "SINGLE published azeotropic VLE data point for methanol-toluene: Burke, D. E.; Williams, "
            "G. C.; Plank, C. A. (1964) 'Vapor-Liquid Equilibria for the Methanol-Toluene System.' "
            "J. Chem. Eng. Data 9(2):212-214, DOI 10.1021/je60021a018. Azeotrope datum (x_methanol=0.887 "
            "mole fraction, T=337.02 K, P=101.3 kPa) as reported and re-cited in He, S.; Fan, W.; Huang, "
            "H.; Gao, J.; Xu, D.; Ma, Y.; Zhang, L.; Wang, Y. (2021) 'Separation of the Azeotropic Mixture "
            "Methanol and Toluene Using Extractive Distillation...' ACS Omega 6(50):34736-34743, DOI "
            "10.1021/acsomega.1c05164 (open access, PMC8697408). Inversion formula (standard, e.g. Smith, "
            "Van Ness & Abbott, Introduction to Chemical Engineering Thermodynamics): at an azeotrope "
            "x_i=y_i so gamma_i=P/P_i^sat(T) directly; A12=ln(g1)(1+x2*ln(g2)/(x1*ln(g1)))^2, "
            "A21=ln(g2)(1+x1*ln(g1)/(x2*ln(g2)))^2. No activity coefficient value used in this audit is "
            "fabricated or reverse-engineered from this module's own claims -- both inputs (Antoine "
            "coefficients, azeotrope datum) are independent published physical constants.",
        "van_laar_fit_result": diag_a["van_laar_fit_from_azeotrope"],
        "proxy_caveat": (
            "The module's carryover blends contain m-xylene, not toluene. A direct methanol + o-xylene "
            "VLE dataset with fitted Van Laar/Wilson parameters exists in the literature (Costa Lopez, J.; "
            "Garvin, A.; Espana, F. J. (1995) 'Vapor-Liquid Equilibrium Data for Methanol, Ethanol, Methyl "
            "Acetate, Ethyl Acetate, and o-Xylene at 101.3 kPa.' J. Chem. Eng. Data 40(5):1067-1071, DOI "
            "10.1021/je00021a008) but its full text was NOT obtainable during this fire (pubs.acs.org "
            "WebFetch returned HTTP 403; the OSTI.gov abstract mirror returned a socket error both retries). "
            "Toluene and m-xylene are both simple monocyclic alkylbenzenes of closely comparable polarity "
            "(Hildebrand solubility parameters approximately 18.2 and 18.0 MPa^0.5 respectively); the "
            "mechanism of the positive deviation -- disruption of methanol self-association (H-bonding) by "
            "a non-polar aromatic diluent -- is the same for both, and m-xylene's activity coefficient for "
            "dilute methanol is expected to be the SAME ORDER OF MAGNITUDE as toluene's, not smaller. This "
            "audit uses toluene data as a declared BOUNDING PROXY for a falsification check, not as a "
            "system-specific replacement value for m-xylene -- flagged below as a residual data gap."
        ),
        "independent_recomputation": (
            "Molar masses re-derived from SMILES via RDKit independently of the module's own cache; mole "
            "fractions re-derived from the module's published mass fractions independently of the module's "
            "own diagnostic; pure-component VHR(T) recomputed from the module's own pinned Antoine "
            "coefficients and OSHA PEL denominators (public physical/regulatory constants, reused not "
            "trusted from the module's derived outputs). Non-ideal contribution isolates methanol's "
            "activity coefficient exactly the way the module's OWN gamma_crit metric is defined (others "
            "held at gamma=1), so the comparison is apples-to-apples against the receipt's own declared "
            "sensitivity metric."
        ),
        "two_replay_byte_stability": {
            "diagnostic_canonical_sha256": sha(diag_a_bytes),
            "diagnostic_runB_sha256": sha(diag_b_bytes),
            "byte_identical": two_replay_byte_identical,
        },
    },
    "findings": {
        "gamma_methanol_infinite_dilution_in_toluene": diag_a["van_laar_fit_from_azeotrope"][
            "gamma1_infinite_dilution_methanol_in_toluene"],
        "dominance_flips": flips_summary,
        "n_blends_flipped": len({f["blend_id"] for f in flips_summary}),
        "n_temperature_points_flipped": len(flips_summary),
        "flips_at_every_envelope_temperature": all(
            any(f["blend_id"] == bid and f["T_C"] == t for f in flips_summary)
            for bid in ("wash_carryover_methanol_1pct", "wash_carryover_methanol_3pct")
            for t in (15.0, 25.0, 40.0)
        ),
        "interpretation": (
            "At every T in the module's own 15-40C application envelope, the van-Laar activity "
            "coefficient for methanol implied by a single published methanol-toluene azeotrope point "
            "(4.81-5.90, depending on blend and T) exceeds the receipt's own reported gamma_crit "
            "threshold for methanol to overtake m_xylene as dominant contributor (1.17-4.17 across the "
            "two affected blends and three temperatures) by a wide margin -- not a marginal or "
            "boundary-adjacent result. Under this real (published, non-fabricated) non-ideality, methanol "
            "is the dominant MHI_sat contributor in BOTH wash_carryover_methanol_1pct and "
            "wash_carryover_methanol_3pct at every envelope temperature, reversing the ideal-solution "
            "receipt's stated dominant_contributor=m_xylene for both blends. Because dominance already "
            "flips at the LOWEST tested carryover level (1 wt%), the true dominance-crossover mass "
            "fraction is at or below 1 wt% methanol -- the receipt's closed-form estimate of 3.7171 wt% "
            "(and its claim that this is 'bracketed at all T' between the 3pct and 6pct blends) is "
            "refuted as a substantial UNDERESTIMATE of how little methanol carryover is needed to govern "
            "the blend's inhalation-hazard ventilation target. The wash_carryover_methanol_6pct blend is "
            "unaffected (already methanol-dominant under both the ideal and the real-gamma model, "
            "gamma_crit undefined because methanol is already dominant) -- this audit does not disturb "
            "that blend's conclusion, sharpening rather than reversing it."
        ),
        "downstream_consequence_for_h0_pure_worst_actor": (
            "The KPI's H0_PURE_WORST_ACTOR hypothesis ('the constituent with the highest pure-component "
            "VHR is the dominant blend contributor') is reported REFUTED, citing wash_carryover_methanol_"
            "1pct and _3pct (among others) as the blends where the pure worst actor (methanol) is NOT "
            "dominant. Under the real, published non-ideality this audit supplies, methanol IS dominant in "
            "both of those blends -- so for these two specific blends H0_PURE_WORST_ACTOR would actually "
            "HOLD under real physics, the opposite of the ideal-model conclusion the KPI reports for them. "
            "This does not fully overturn H0_PURE_WORST_ACTOR's overall REFUTED verdict (aromatic_100_"
            "surrogate, which contains no alcohol, is untouched by this audit and independently supports "
            "the refutation), but it does refute the SPECIFIC per-blend dominance calls for the two "
            "methanol-carryover blends the receipt cites as supporting evidence."
        ),
    },
    "verdict": "CLAIM_REFUTED",
    "verdict_summary": (
        "REFUTED. Applying a real activity coefficient for methanol in an aromatic-hydrocarbon solvent "
        "(van Laar model fit to a single published methanol-toluene azeotrope datum, Burke/Williams/Plank "
        "1964) at the module's own blend compositions shows methanol's true contribution exceeds the "
        "receipt's own reported gamma_crit threshold at every temperature in the module's 15-40C envelope "
        "for both wash_carryover_methanol_1pct and wash_carryover_methanol_3pct, flipping the dominant "
        "contributor from m_xylene to methanol in both. The closed-form dominance-crossover estimate "
        "(3.7171 wt% methanol) is therefore refuted as an underestimate -- the real crossover is at or "
        "below the lowest tested carryover level, 1 wt%. Toluene-for-m-xylene is a declared bounding "
        "proxy (a direct methanol+o-xylene literature source exists but was paywalled this fire); flagged "
        "as a residual data gap, not hidden."
    ),
    "does_not_close": [
        "Does not modify the attacked KPI, its scientific receipt, dominant_contributor fields, "
        "crossover_predicted_mass_fraction_25C, or any procurement/ventilation-priority output -- "
        "disclosure only, per the conservative-default posture established by W-EHS1/EHS-HCOMP: a "
        "safety-relevant quantitative correction (which solvent to prioritise for ventilation) is a "
        "human-reviewable change, not an unreviewed mechanical patch.",
        "Uses toluene VLE as a declared bounding proxy for m-xylene, not system-specific data -- a "
        "methanol + o-xylene direct source is identified (Costa Lopez, Garvin & Espana 1995, DOI "
        "10.1021/je00021a008) but its full text was not obtainable this fire; a repair/verify fire "
        "with library or publisher access could tighten this to system-exact data.",
        "Does not attack H0_MASS_SURROGATE, the exactness identity gate, the aromatic_100_surrogate "
        "finding, or any single-substance VHR/GHS/OSHA-attribution receipt -- scope is confined to the "
        "two methanol-carryover blends' dominance/crossover claim.",
        "Van Laar parameters are treated as T-independent over 15-40C (the model's standard simplifying "
        "assumption, declared, not concealed) -- a temperature-dependent activity-coefficient model would "
        "refine but is not expected to reverse this finding given the wide (roughly 4x) margin between "
        "gamma_crit and the van-Laar gamma at every tested T.",
        "AUDIT_ONLY: no OSHA compliance, exposure-assessment, ventilation-design, procurement, or "
        "regulatory-closure authority.",
    ],
    "references": [
        "Burke, D. E.; Williams, G. C.; Plank, C. A. (1964) 'Vapor-Liquid Equilibria for the "
        "Methanol-Toluene System.' J. Chem. Eng. Data 9(2): 212-214. DOI 10.1021/je60021a018.",
        "He, S.; Fan, W.; Huang, H.; Gao, J.; Xu, D.; Ma, Y.; Zhang, L.; Wang, Y. (2021) 'Separation of "
        "the Azeotropic Mixture Methanol and Toluene Using Extractive Distillation: Entrainer "
        "Determination, Vapor-Liquid Equilibrium Measurement, and Modeling.' ACS Omega 6(50): 34736-34743. "
        "DOI 10.1021/acsomega.1c05164. Open access, PMC8697408.",
        "Van Laar, J. J. (1910) 'The vapor pressure of binary mixtures.' Z. Phys. Chem. 72: 723-751 "
        "(original two-parameter activity-coefficient model; inversion-from-azeotrope formula as given in "
        "standard texts, e.g. Smith, J. M.; Van Ness, H. C.; Abbott, M. M. Introduction to Chemical "
        "Engineering Thermodynamics, 7th ed., McGraw-Hill, 2005, Ch. 12).",
        "Costa Lopez, J.; Garvin, A.; Espana, F. J. (1995) 'Vapor-Liquid Equilibrium Data for Methanol, "
        "Ethanol, Methyl Acetate, Ethyl Acetate, and o-Xylene at 101.3 kPa.' J. Chem. Eng. Data 40(5): "
        "1067-1071. DOI 10.1021/je00021a008. (Direct methanol+o-xylene source; identified but full text "
        "not obtained this fire -- see proxy_caveat and does_not_close.)",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.sourceability-ehs-audit-z-ehs-vanlaar+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", OUT_PATH)
print("self_verify_signature", True)
print("envelope_sha256", sha(OUT_PATH.read_bytes()))
