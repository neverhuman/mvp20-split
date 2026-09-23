#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V-A06 independent-verify receipt for
amphora-molecule-generator. Construction replicated from
amphora-molecule-generator/evidence/phase0/repairs/R-A06/work/sign_ra06_repair.py
(pae, load_seed, payloadType, envelope fields, trust-store key derivation).

VERIFY-ONLY: does not supersede, modify, or delete any existing signed
artifact, the ledger, any mission.md front-matter, or the master manifest.
Writes only into evidence/phase0/repairs/V-A06/done/.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-generator"
REP = MOD / "evidence/phase0/repairs"
WORK, DONE = REP / "V-A06/work", REP / "V-A06/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

REL = "amphora-molecule-generator"
R_A06_REL = f"{REL}/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json"
SRC_DIAG_REL = f"{REL}/evidence/audit/molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json"
R_A06 = ROOT / R_A06_REL
SRC_DIAG = ROOT / SRC_DIAG_REL


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


# ---------------------------------------------- two-replay gate over the diagnostic
canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

harness_sha = sha((WORK / "verify_va06.py").read_bytes())
r_a06_sha = sha(R_A06.read_bytes())
src_diag_sha = sha(SRC_DIAG.read_bytes())

# ---------------------------------------------- keys / trust anchoring
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key not anchored in phase0 trust store"

esc = diag["escalation_active_hydrogen_functionality_check"]
n_mismatch = esc["n_amine_sites2_flagged_difunctional_but_active_nh_ne_2"]
refuted = n_mismatch > 0

body_obj = {
    "schema": "amphora.molecule-generator.v-a06-repair-verify.v1",
    "verify_item": "V-A06",
    "target_repair_item": "R-A06",
    "module_id": REL,
    "module": REL,
    "authority": "AUDIT_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_asserted": False,
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
    "run_type": "INDEPENDENT_REPAIR_VERIFICATION",

    "promotes_authority": False,
    "human_review_performed": False,
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "supersedes": None,

    "claim_under_verify": (
        f"{R_A06_REL} :: the interactive repair R-A06 (corrected feasible-fraction "
        "Clopper-Pearson CI to [0.9075,1.0000], corrected valid-unique-difunctional-"
        "feasible yield from 38/38 to 29/38 under the gate definition amine_sites==2, "
        "and republished IntDiv_1 diversity family-resolved) withstands independent "
        "adversarial verification."
    ),

    "artifacts": {
        "target_r_a06_done_receipt": {"path": R_A06_REL, "sha256": r_a06_sha},
        "source_diagnostic": {"path": SRC_DIAG_REL, "sha256": src_diag_sha},
        "verifier_script": {
            "path": f"{REL}/evidence/phase0/repairs/V-A06/work/verify_va06.py",
            "sha256": harness_sha},
        "verify_report_run1_sha256": diag_sha,
        "verify_report_run2_sha256": sha(runB),
    },

    "checks": {
        "1_precondition_done_receipt_exists": True,
        "2_amine_sites_independently_recomputed_from_smiles_not_diagnostic_table": True,
        "2_amine_sites_parity_with_diagnostic_table": diag["amine_sites_parity_with_diagnostic"],
        "2_active_nh_independently_recomputed_from_smiles_not_diagnostic_table": True,
        "2_active_nh_parity_with_diagnostic_table": diag["active_nh_parity_with_diagnostic"],
        "3_independent_yield_by_amine_sites_eq_2": diag["independent_yield_by_amine_sites_eq_2"],
        "3_r_a06_claimed_yield": diag["r_a06_claimed_yield"],
        "3_independent_yield_matches_r_a06_under_its_own_stated_gate": diag["independent_yield_matches_r_a06"],
        "4_clopper_pearson_independently_recomputed_fresh_k_n": True,
        "4_clopper_pearson_matches_r_a06_4dp": diag["clopper_pearson_independent"]["matches_r_a06_4dp"],
        "5_family_intdiv1_independently_recomputed_own_fingerprint_code": True,
        "5_f1_matches_r_a06_4dp": diag["f1_matches_r_a06_4dp_at_r2"],
        "5_f2_matches_r_a06_4dp": diag["f2_matches_r_a06_4dp_at_r2"],
        "5_f1_near_degeneracy_survives_radius3_adjacent_stress": diag["f1_near_degenerate_survives_radius3_stress"],
        "5_f2_near_degeneracy_survives_radius3_adjacent_stress": diag["f2_near_degenerate_survives_radius3_stress"],
        "6_escalation_active_hydrogen_functionality_n_mismatch_within_r_a06_29": n_mismatch,
        "6_escalation_n_true_difunctional_by_active_h_among_all_38": esc["n_true_difunctional_by_active_h_eq_2"],
        "6_escalation_mda_ddm_active_nh": esc["mda_ddm_known_textbook_case"]["active_nh"],
        "all_checks_pass_under_r_a06_own_definition": bool(
            diag["amine_sites_parity_with_diagnostic"]
            and diag["independent_yield_matches_r_a06"]
            and diag["clopper_pearson_independent"]["matches_r_a06_4dp"]
            and diag["f1_matches_r_a06_4dp_at_r2"]
            and diag["f2_matches_r_a06_4dp_at_r2"]),
        "escalation_check_refutes_corrected_claim": refuted,
    },

    "escalation_attack": {
        "name": "active_hydrogen_functionality_convention_cross_check",
        "description": (
            "R-A06's own self-check only verified internal consistency with its "
            "stated gate definition ('difunctional == amine_sites==2', i.e. "
            "nitrogen-ATOM count). It never cross-validated that definition against "
            "the active-HYDROGEN-count functionality convention that (a) this same "
            "module's superseded receipt O1 already cites Lee & Neville 1967 for "
            "('cure_reactivity_gate' theory_reference), (b) is the convention this "
            "portfolio itself uses elsewhere for epoxy-amine curing stoichiometry "
            "and Flory-Stockmayer gelation math (AHEW = 28052.8/amine_value; "
            "amine-N-H active-site property receipts), and (c) is the textbook "
            "convention in the published epoxy literature -- e.g. MDA/DDM "
            "(4,4'-diaminodiphenylmethane), one of the 38 accepted proposals here, "
            "is universally classified as a TETRAfunctional curing agent (AHEW = "
            "MW/4, approx 49.5 g/eq) precisely because a primary -NH2 group reacts "
            "TWICE with epoxide, despite having only 2 nitrogen atoms."
        ),
        "falsification_criterion": {
            "statement": "R-A06 republishes 29/38 accepted proposals as 'difunctional' hardeners under amine_sites==2. If ANY of those 29 fails to have active_nh==2 under a fresh, independent RDKit re-derivation from the raw canonical_smiles (not the diagnostic's own active_nh column), the corrected 'difunctional' claim is falsified as chemically mislabeled under the standard active-hydrogen functionality convention.",
            "would_survive_if": "all 29 amine_sites==2 proposals independently re-derive to active_nh==2 as well.",
        },
        "observed": {
            "n_amine_sites2_but_active_nh_ne_2": n_mismatch,
            "n_amine_sites2_total": 29,
            "n_true_difunctional_active_h_eq_2_among_all_38": esc["n_true_difunctional_by_active_h_eq_2"],
            "all_29_are_active_nh_4_primary_primary_diamines": True,
            "mda_ddm_case": esc["mda_ddm_known_textbook_case"],
        },
        "result": (
            "REFUTES. All 29 proposals R-A06 republishes as 'difunctional' are "
            "primary,primary diamines with independently re-derived active_nh=4 "
            "(TETRAfunctional under the active-hydrogen convention), including "
            "MDA/DDM -- the textbook tetrafunctional curing agent. Zero of the 38 "
            "accepted proposals have active_nh==2. Under the active-hydrogen "
            "functionality convention this module's own theory_reference (Lee & "
            "Neville 1967) and the wider portfolio's AHEW/Flory-Stockmayer receipts "
            "use, the true 'difunctional' (f=2) yield among these 38 accepted "
            "proposals is 0/38, not 29/38. R-A06's arithmetic re-derivation of "
            "'amine_sites==2' is internally correct and reproduces exactly -- but "
            "the corrected headline claim ('29/38 ... DIFUNCTIONAL ... hardener "
            "proposals') mislabels a set of tetrafunctional hardeners as "
            "difunctional, the same species of chemical-labeling error R-A06 was "
            "created to fix in the first place, just recurring one layer deeper."
        ),
    },

    "clopper_pearson_independent": diag["clopper_pearson_independent"],
    "family_resolved_intdiv1_independent": diag["family_resolved_intdiv1_independent"],

    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, qualification, regulatory, or FTO authority.",
        "Verify-only: writes no new supersession, edits no existing signed artifact, mission front-matter, or the master manifest. Confined to evidence/phase0/repairs/V-A06/.",
        "Does not re-derive or dispute R-A06's Clopper-Pearson interval or family-resolved IntDiv_1 corrections -- both independently reproduce exactly (Clopper-Pearson 4dp match; F1/F2 IntDiv_1 4dp match).",
        "Does not assert a corrected difunctional yield number of its own (e.g. 0/38) as a new headline -- that determination, if pursued, belongs to a follow-up repair item (R-A06 v2), not this verify receipt.",
        "Does not modify, delete, or re-sign R-A06 or any receipt it supersedes; all are left byte-intact on disk.",
        "Radius-3 adjacent-fingerprint stress test (diagnostic only, not part of R-A06's own claim) finds F1_polyethyleneamine's near-degeneracy is radius-sensitive (IntDiv_1 rises from 0.1851 to 0.2621, just above the 0.25 decision threshold at radius=3) while F2 remains robust (0.0870 to 0.2155); this is a minor caveat on the diversity correction's robustness, not by itself grounds for CLAIM_REFUTED, and does not affect the verdict here.",
    ],

    "refutation_would_have_shown": [
        "an independently-written, from-scratch RDKit re-derivation of amine_sites or active_nh from the 38 raw canonical_smiles disagreeing with the diagnostic's own table (checked: 0 mismatches, full parity)",
        "the independently re-derived difunctional-by-amine_sites yield disagreeing with R-A06's claimed 29/38 (checked: exact match)",
        "the independently re-derived Clopper-Pearson interval or family IntDiv_1 values disagreeing with R-A06's corrected_values to 4dp (checked: exact match on both)",
        "any amine_sites==2 proposal independently re-deriving to active_nh==2 as well, i.e. genuinely difunctional under the active-hydrogen convention (checked: 0 of 29 -- this is the finding that refutes the claim)",
    ],

    "verdict": "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED",
    "repair_status": "fix_landed_refuted" if refuted else "confirmed_holds",
    "headline": (
        "V-A06 independent verify of repair R-A06: independently re-derived amine_sites "
        "and active_nh for all 38 accepted proposals directly from canonical_smiles with "
        "a freshly-written RDKit harness (not R-A06's own script, not trusting the "
        "diagnostic's own amine_sites/active_nh columns as ground truth) -- full parity "
        "(0 mismatches) confirms R-A06's base data and its Clopper-Pearson (4dp exact) "
        "and family-resolved IntDiv_1 (4dp exact, F1/F2) corrections all independently "
        "reproduce. R-A06's own internal-consistency re-check of 'amine_sites==2' also "
        "reproduces exactly (29/38). BUT escalating past R-A06's self-check: cross-"
        "validating the 29 'difunctional' proposals against the active-hydrogen "
        "functionality convention (AHEW basis) that this module's own theory_reference "
        "(Lee & Neville 1967) and the wider portfolio's AHEW/Flory-Stockmayer receipts "
        "already use shows all 29 are primary,primary diamines with active_nh=4 "
        "(tetrafunctional), including MDA/DDM, the textbook tetrafunctional curing "
        "agent. 0 of the 38 accepted proposals have active_nh==2. The corrected "
        "'29/38 difunctional' headline is therefore chemically mislabeled under the "
        "field-standard functionality convention. Verdict: CLAIM_REFUTED."
    ),

    "theory_reference": {
        "active_hydrogen_functionality_convention": "AHEW = MW / active_hydrogen_count; each primary -NH2 contributes 2 reactive sites (functionality), each secondary -NH- contributes 1.",
        "functionality_reference": "Lee & Neville 1967 Handbook of Epoxy Resins (McGraw-Hill) -- same source R-A06's own superseded receipt O1 cites for its cure_reactivity_gate",
        "gelation_functionality_theory": "Flory 1953 Principles of Polymer Chemistry, Cornell Univ. Press, ch. IX (Flory-Stockmayer functionality f = reactive-hydrogen count, not heteroatom count)",
        "mda_textbook_reference": "MDA/DDM (4,4'-diaminodiphenylmethane) is standardly listed as a tetrafunctional epoxy curing agent (AHEW approx 49.5 g/eq, MW 198.26 / 4 active H) in published epoxy formulation references.",
        "amine_site_smarts": "[NX3;!$(NC=O);!$(N=*);!$(N#*);!a] -- non-aromatic sp3 nitrogen, excludes amide/imine/nitrile/nitro/aromatic (independently re-implemented fresh in this verify harness)",
        "toolkit": "RDKit 2026.03.2; scipy 1.16.3",
    },

    "reproducibility": {
        "two_replay_sha256_gate": {"status": "PASS", "replays": 2,
                                    "replay_a_sha256": diag_sha, "replay_b_sha256": sha(runB),
                                    "byte_stable": canon == runB},
        "rdkit_version": diag["rdkit_version"],
        "replay_method": (
            "Independent RDKit re-derivation on xbabe2: amine_sites and active_nh "
            "recomputed from raw canonical_smiles with a freshly-authored SMARTS "
            "harness (not R-A06's run_ra06_repair.py); Clopper-Pearson recomputed via "
            "scipy.stats.beta.ppf with fresh k/n counted from the diagnostic's own "
            "feasible_sa_below_6 column; family IntDiv_1 recomputed with an "
            "independently-instantiated RDKit Morgan/ECFP r2/2048 generator, plus an "
            "r3/2048 adjacent-radius stress variant. Harness deterministic (no RNG, "
            "no wall-clock); run twice to byte-identical output."),
    },

    "rights_posture": {
        "external_dataset_used": False,
        "new_external_data_acquired": False,
        "quarantined_data_touched": False,
        "input_smiles": "read verbatim from the hash-locked molgen-deterministic-grammar-yield-v1 diagnostic (published epoxy-amine scaffold families)",
        "methods": "Clopper & Pearson 1934 exact binomial; RDKit (BSD-licensed) SMARTS/Morgan/ECFP fingerprints and Tanimoto; all published open methods",
        "note": "No PI1M, Polyverse, ST-19168, or CONTEXT_ONLY data opened by this verify.",
    },

    "provenance": {
        "harness_sha256": {"verify_va06.py": harness_sha},
        "source_diagnostic_sha256": {SRC_DIAG_REL: src_diag_sha},
        "target_receipt_sha256": {R_A06_REL: r_a06_sha},
        "inputs_are_read_only": True,
    },

    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-verify receipt under evidence/phase0/repairs/V-A06/done/",
        "authority": "AUDIT_ONLY",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
        "trust_anchored_in_phase0_promotion_store": bool(eval_pin),
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony"},
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
assert body == json.dumps(body_obj, indent=2, sort_keys=True).encode(), "body not byte-stable"
ptype = "application/vnd.amphora.molecule-generator-v-a06-repair-verify+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("verdict", body_obj["verdict"])
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
